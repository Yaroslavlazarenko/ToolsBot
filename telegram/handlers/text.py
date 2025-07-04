from aiogram import Router, F, types

router = Router()

@router.message(F.text)
async def handler(message: types.Message) -> None:
    