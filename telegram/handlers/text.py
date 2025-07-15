import logging
from aiogram import Router, F, types
from agents.orchestrator_agent import OrchestratorAgent
from telegram.responder import TelegramResponder
from core.exceptions import ServiceError
import asyncio # <--- Добавляем импорт asyncio

router = Router()
logger = logging.getLogger(__name__) # Используем стандартный способ получения логгера

# <--- Добавляем новую асинхронную функцию для фоновой обработки
async def _process_request_in_background(
    orchestrator: OrchestratorAgent, 
    responder: TelegramResponder, 
    message: types.Message, 
    processing_msg: types.Message
):
    """
    Выполняет основную логику обработки запроса в фоне.
    """
    try:
        response_data = await orchestrator.process_request(message.text or "")
        await responder.send_response(message, response_data)
        user_id = message.from_user.id if message.from_user else "unknown"
        logger.info(f"Request processing completed for user {user_id}")
    except ServiceError as e:
        user_id = message.from_user.id if message.from_user else "unknown"
        logger.error(f"Service error occurred for user {user_id}: {e}")
        error_response = {'type': 'text', 'content': 'An error occurred while processing your request. Please try again later.'}
        await responder.send_response(message, error_response)
    except Exception as e:
        user_id = message.from_user.id if message.from_user else "unknown"
        logger.exception(f"Critical unhandled error for user {user_id}.")
        error_response = {'type': 'text', 'content': 'A critical internal error occurred.'}
        await responder.send_response(message, error_response)
    finally:
        try:
            await processing_msg.delete()
        except Exception as e:
            user_id = message.from_user.id if message.from_user else "unknown"
            logger.warning(f"Could not delete 'Received. Processing...' message for {user_id}: {e}")
            pass


@router.message(F.text)
async def text_message_handler(message: types.Message, orchestrator: OrchestratorAgent, responder: TelegramResponder):
    if not message.text:
        return
    
    # 1. Немедленно отправляем подтверждение
    processing_msg = await message.answer("Received. Processing...")
    
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info(f"Message received from user {user_id}. Starting background processing.")

    # 2. Запускаем основную логику обработки в фоновой задаче
    asyncio.create_task(
        _process_request_in_background(orchestrator, responder, message, processing_msg)
    )

    # 3. Обработчик завершается немедленно, отправляя 200 OK в Telegram
    # (Неявно возвращается, так как нет await или других операций)