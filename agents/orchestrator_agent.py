import os
import logging
import asyncio
from typing import Dict, Union

from aiogram import types
from aiogram.fsm.context import FSMContext
from agents.router_agent import RouterAgent
from use_cases.function_handler import FunctionHandler
from telegram.responder import TelegramResponder
from core.task_manager import task_manager, TaskIdentifier
from telegram.states import ProcessingState

OrchestratorResponse = Dict[str, Union[str, bool]]

class OrchestratorAgent:
    def __init__(self, router_agent: RouterAgent, function_handler: FunctionHandler, responder: TelegramResponder):
        self.router_agent = router_agent
        self.function_handler = function_handler
        self.responder = responder
        self.logger = logging.getLogger("OrchestratorAgent")

    async def process_request(self, user_text: str, message: types.Message, state: FSMContext) -> OrchestratorResponse:
        routing_decision = await self.router_agent.route(user_text)
        
        if not routing_decision or "function_to_call" not in routing_decision:
            return {'type': 'text', 'content': 'Я не смог понять ваш запрос.'}

        function_to_call = routing_decision.get("function_to_call")
        language = routing_decision.get("language", "English")
        current_state_str = await state.get_state()

        if current_state_str == ProcessingState.is_processing and function_to_call == "analyze_video_content":
            return {'type': 'text', 'content': "Пожалуйста, подождите, предыдущая обработка видео еще не завершена."}

        if function_to_call == "analyze_video_content":
            await state.update_data(
                original_prompt=user_text,
                language=language
            )
            self.logger.info(f"Saved to state: prompt='{user_text}', language='{language}'")
            return await self.function_handler.estimate_and_propose_analysis(user_text, message)
        
        if hasattr(self.function_handler, function_to_call):
            method_to_call = getattr(self.function_handler, function_to_call)
            final_result = await method_to_call(user_text)
            return self._format_response(final_result)
        else:
            return {'type': 'text', 'content': f'Internal error: handler for {function_to_call} not found.'}

    # --- ВОТ ВОССТАНОВЛЕННЫЕ МЕТОДЫ ---

    async def launch_analysis_task(self, video_id: str, original_message: types.Message, state: FSMContext):
        """Запускает тяжелую задачу анализа в фоне и сохраняет ее в TaskManager."""
        task_identifier: TaskIdentifier = (original_message.chat.id, original_message.message_id)
        task = asyncio.create_task(
            self._run_analysis_and_respond(video_id, original_message, task_identifier, state)
        )
        task_manager.add_task(task_identifier, task)

    async def _run_analysis_and_respond(
        self, video_id: str, message: types.Message, task_identifier: TaskIdentifier, state: FSMContext
    ):
        """Обертка для фоновой задачи: выполняет анализ, обрабатывает результат, ошибки и отмену."""
        try:
            fsm_data = await state.get_data()
            original_prompt = fsm_data.get("original_prompt", "Summarize this video.")
            language = fsm_data.get("language", "English")
            self.logger.info(f"Retrieved from state: prompt='{original_prompt}', language='{language}'")

            result_str = await self.function_handler.execute_video_analysis(
                video_id=video_id,
                original_user_prompt=original_prompt,
                language=language,
                message=message
            )
            
            response_data = self._format_response(result_str)
            await self.responder.send_response(message, response_data)
            await message.edit_text("✅ Обработка успешно завершена.", reply_markup=None)

        except asyncio.CancelledError:
            self.logger.warning(f"Task {task_identifier} was cancelled by user {message.chat.id}.")
            await message.edit_text("✅ Обработка успешно отменена.")

        except Exception as e:
            self.logger.error(f"Task {task_identifier} failed for user {message.chat.id}: {e}", exc_info=True)
            error_response = {'type': 'text', 'content': f'Произошла критическая ошибка: {e}'}
            await self.responder.send_response(message, error_response)
            await message.edit_text("❌ Во время обработки произошла ошибка.", reply_markup=None)
        finally:
            self.logger.info(f"Cleaning up for task {task_identifier}, user {message.chat.id}.")
            await state.clear()
            task_manager.remove_task(task_identifier)

    def _format_response(self, result: str) -> OrchestratorResponse:
        """Форматирует финальный результат (строку) в словарь для Responder."""
        if not result:
            self.logger.error("A function handler returned a None or empty result.")
            return {'type': 'text', 'content': "К сожалению, произошла внутренняя ошибка..."}
        if isinstance(result, str) and os.path.isfile(result):
            return {'type': 'document', 'content': result, 'caption': 'Ваш детальный анализ видео готов.'}
        else:
            return {'type': 'text', 'content': str(result)}