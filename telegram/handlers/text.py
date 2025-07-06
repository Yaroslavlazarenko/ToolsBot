from aiogram import Router, F, types
from app.services import youtube_tool_service

from telegram.utils.message import send_message

router = Router()

@router.message(F.text)
async def handler(message: types.Message) -> None:
    response = await youtube_tool_service.generate(message.text)
    await send_message(message, response)