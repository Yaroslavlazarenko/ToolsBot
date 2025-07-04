from aiogram import types

TELEGRAM_MAX_MESSAGE_LENGTH = 4096

async def send_long_message(message: types.Message, text: str):
    """
    Асинхронная функция для отправки длинного текста, разбивая его на части.
    Старается не разрывать слова.
    """
    while len(text) > 0:
        if len(text) <= TELEGRAM_MAX_MESSAGE_LENGTH:
            await message.answer(text)
            break

        chunk = text[:TELEGRAM_MAX_MESSAGE_LENGTH]
        last_space = chunk.rfind(' ')
        last_newline = chunk.rfind('\n')
        
        split_pos = max(last_space, last_newline)

        if split_pos == -1:
            split_pos = TELEGRAM_MAX_MESSAGE_LENGTH

        await message.answer(text[:split_pos])
        
        text = text[split_pos:].lstrip()