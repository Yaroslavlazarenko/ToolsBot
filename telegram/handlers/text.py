from aiogram import Router, F, types
from models.gemini_with_tools import generate_content

from tools.telegram.send_long_message import send_long_message

router = Router()

@router.message(F.text)
async def handler(message: types.Message) -> None:
    response = await generate_content(message.text)
    await send_long_message(message, response)
