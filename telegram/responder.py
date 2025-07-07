import os
from aiogram import types
from aiogram.types import FSInputFile
from telegram.utils.message import send_message

from typing import Mapping

class TelegramResponder:
    async def send_response(self, message: types.Message, response_data: Mapping[str, str | bool]):

        response_type = response_data.get('type')
        content = response_data.get('content')

        try:
            if response_type == 'text':

                if isinstance(content, str):
                    await send_message(message, content)
                else:
                    await send_message(message, "Internal error: invalid content for text response.")
            
            elif response_type == 'document':

                if isinstance(content, str):

                    caption_value = response_data.get('caption')
                    caption_text = caption_value if isinstance(caption_value, str) else None

                    await self._send_document(message, content, caption_text)
                else:
                    await send_message(message, "Internal error: file path is missing for document response.")

            else:
                await send_message(message, "Internal error: failed to form response.")
        except Exception as e:
            await send_message(message, "Failed to send response due to an unexpected error.")

    async def _send_document(self, message: types.Message, file_path: str, caption: str | None):

        if not file_path or not os.path.isfile(file_path):
            await send_message(message, "Internal error: report file not found or path is invalid.")
            return
        
        input_file = FSInputFile(file_path)
        await message.answer_document(input_file, caption=caption)

        try:
            os.remove(file_path)
        except OSError as e:
            return