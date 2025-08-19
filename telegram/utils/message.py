import html

from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

MAX_MESSAGE_LENGTH = 4096

async def send_message(message: Message, text: str):
    if not isinstance(message, Message):
        return
    if not isinstance(text, str):
        await message.answer("Internal error: response is not a string.")
        return
    if not text.strip():
        return
    safe_text = html.escape(text)
    if len(safe_text) <= MAX_MESSAGE_LENGTH:
        try:
            await message.answer(safe_text)
        except TelegramBadRequest as e:
            await message.answer("An error occurred while trying to send the response.")
    else:
        parts = []
        while len(safe_text) > 0:
            if len(safe_text) > MAX_MESSAGE_LENGTH:
                part = safe_text[:MAX_MESSAGE_LENGTH]
                last_newline = part.rfind('\n')
                last_space = part.rfind(' ')
                cut_off = max(last_newline, last_space)
                if cut_off == -1:
                    cut_off = MAX_MESSAGE_LENGTH
                parts.append(safe_text[:cut_off])
                safe_text = safe_text[cut_off:].lstrip()
            else:
                parts.append(safe_text)
                break
        for part in parts:
            if part.strip():
                await message.answer(part)