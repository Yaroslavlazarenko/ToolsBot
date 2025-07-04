from aiogram import Router, F, types
from models.gemini import generate_content

router = Router()

@router.message(F.text)
async def handler(message: types.Message) -> None:
    response = await generate_content(message.text)
    await message.answer(response)
    