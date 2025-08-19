import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from agents.orchestrator_agent import OrchestratorAgent
from telegram.responder import TelegramResponder

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text)
async def text_message_handler(
    message: types.Message,
    orchestrator: OrchestratorAgent,
    responder: TelegramResponder,
    state: FSMContext
):
    user_text = message.text
    if not user_text:
        return

    processing_msg = await message.answer("Получено. Обрабатываю запрос...")
    try:
        # Передаем state в оркестратор, где будет происходить вся логика
        response_data = await orchestrator.process_request(user_text, message=message, state=state)
        
        if response_data.get('type') != 'confirmation':
             await processing_msg.delete()
        else:
            await processing_msg.edit_text("Оценил ваш запрос:")
            
        await responder.send_response(message, response_data)

    except Exception as e:
        logger.error(f"Critical error in text handler: {e}", exc_info=True)
        try:
            await processing_msg.delete()
        except Exception:
            pass
        
        error_response = {'type': 'text', 'content': f'Произошла критическая ошибка. Пожалуйста, попробуйте позже.'}
        await responder.send_response(message, error_response)