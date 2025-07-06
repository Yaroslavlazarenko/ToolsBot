import html

from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

MAX_MESSAGE_LENGTH = 4096

async def send_message(message: Message, text: str):
    """
    Sends a long message by splitting it into parts if necessary.
    Also sanitizes the text to prevent HTML parsing errors.
    """
    safe_text = html.escape(text)

    if len(safe_text) <= MAX_MESSAGE_LENGTH:
        try:
            # Send the sanitized text
            await message.answer(safe_text)
        except TelegramBadRequest as e:
            print(f"Error sending message even after escaping: {e}")
            await message.answer("An error occurred while trying to send the response.")
    else:
        parts = []
        while len(safe_text) > 0:
            if len(safe_text) > MAX_MESSAGE_LENGTH:
                part = safe_text[:MAX_MESSAGE_LENGTH]
                # Try to find a good place to split (e.g., a newline or space)
                last_newline = part.rfind('\n')
                last_space = part.rfind(' ')
                cut_off = max(last_newline, last_space)
                
                if cut_off == -1: # No good split point found
                    cut_off = MAX_MESSAGE_LENGTH

                parts.append(safe_text[:cut_off])
                safe_text = safe_text[cut_off:].lstrip()
            else:
                parts.append(safe_text)
                break
        
        for part in parts:
            if part.strip():
                await message.answer(part)