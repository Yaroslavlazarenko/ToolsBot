import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from agents.orchestrator_agent import OrchestratorAgent
from telegram.responder import TelegramResponder
from core.exceptions import ServiceError
import asyncio # <--- Добавляем импорт asyncio

router = Router()
logger = logging.getLogger(__name__) # Используем стандартный способ получения логгера

@router.message(F.text)
async def text_message_handler(
    message: types.Message,
    orchestrator: OrchestratorAgent,
    responder: TelegramResponder,
    state: FSMContext  # Мы все еще принимаем state, чтобы передать его дальше
):
    user_text = message.text
    if not user_text:
        return

    processing_msg = await message.answer("Получено. Обрабатываю запрос...")
    try:
        # Передаем state в оркестратор, где и будет происходить вся логика
        response_data = await orchestrator.process_request(user_text, message=message, state=state)
        
        # Улучшение UX: удаляем "Обрабатываю..." только если ответ не требует действий
        if response_data.get('type') != 'confirmation':
             await processing_msg.delete()
        else:
            # Для сообщения с кнопками лучше изменить текст
            await processing_msg.edit_text("Оценил ваш запрос:")
            
        await responder.send_response(message, response_data)
        user_id = message.from_user.id if message.from_user else "unknown"
        logger.info(f"Request processing completed for user {user_id}")
    except ServiceError as e:
        user_id = message.from_user.id if message.from_user else "unknown"
        logger.error(f"Service error occurred for user {user_id}: {e}")
        error_response = {'type': 'text', 'content': 'An error occurred while processing your request. Please try again later.'}
        await responder.send_response(message, error_response)
    except Exception as e:
        try:
            await processing_msg.delete()
        except Exception:
            pass
        
        error_response = {'type': 'text', 'content': f'Произошла критическая ошибка: {e}'}
        await responder.send_response(message, error_response)
