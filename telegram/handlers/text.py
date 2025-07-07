import logging
from aiogram import Router, F, types
from agents.orchestrator_agent import OrchestratorAgent
from telegram.responder import TelegramResponder
from core.exceptions import ServiceError

router = Router()

@router.message(F.text)
async def text_message_handler(message: types.Message, orchestrator: OrchestratorAgent, responder: TelegramResponder):
    if not message.text:
        return
    
    processing_msg = await message.answer("Received. Processing...")

    try:
        response_data = await orchestrator.process_request(message.text)
        await responder.send_response(message, response_data)
    except ServiceError as e:
        logging.error(f"A service error occurred: {e}")
        error_response = {'type': 'text', 'content': 'An error occurred while processing your request. Please try again later.'}
        await responder.send_response(message, error_response)
    except Exception as e:
        logging.exception("A critical unhandled error occurred.")
        error_response = {'type': 'text', 'content': 'A critical internal error occurred.'}
        await responder.send_response(message, error_response)
    finally:
        try:
            await processing_msg.delete()
        except Exception:
            pass