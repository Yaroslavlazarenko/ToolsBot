from aiogram import Router, F, types
from agents.orchestrator_agent import OrchestratorAgent
from telegram.responder import TelegramResponder

router = Router()

@router.message(F.text)
async def text_message_handler(
    message: types.Message,
    orchestrator: OrchestratorAgent,
    responder: TelegramResponder
):
    user_text = message.text
    if not user_text:
        return
    processing_msg = await message.answer("Received. Processing...")
    try:
        response_data = await orchestrator.process_request(user_text)
        await responder.send_response(message, response_data)
    except Exception as e:
        error_response = {'type': 'text', 'content': 'A critical error occurred.'}
        await responder.send_response(message, error_response)
    finally:
        try:
            await processing_msg.delete()
        except Exception:
            pass