import os
from typing import Dict, Union
from aiogram import types
from aiogram.types import FSInputFile
from telegram.utils.message import send_message

class TelegramResponder:
    async def send_response(self, message: types.Message, response_data: Dict[str, Union[str, bool]]):
        response_type = response_data.get('type')
        content = response_data.get('content')
        try:
            if response_type == 'text':
                await send_message(message, content)
            elif response_type == 'document':
                await self._send_document(message, content, response_data.get('caption'))
            else:
                await send_message(message, "Internal error: failed to form response.")
        except Exception as e:
            await send_message(message, "Failed to send response.")

    async def _send_document(self, message: types.Message, file_path: str, caption: str):
        if not os.path.isfile(file_path):
            await send_message(message, "Internal error: report file not found.")
            return
        input_file = FSInputFile(file_path)
        await message.answer_document(input_file, caption=caption)
        try:
            os.remove(file_path)
        except OSError as e:
            return