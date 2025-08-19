import os
from aiogram import types
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.utils.message import send_message
from typing import Dict, Union

# ИЗМЕНЕНО: Импортируем из нового файла, разрывая цикл
from telegram.callback_data import VideoCallback 

class TelegramResponder:
    async def send_response(self, message: types.Message, response_data: Dict[str, Union[str, bool, dict]]):
        response_type = response_data.get('type')
        try:
            if response_type == 'text':
                await send_message(message, response_data.get('content'))
            elif response_type == 'document':
                await self._send_document(message, response_data.get('content'), response_data.get('caption'))
            elif response_type == 'confirmation':
                await self._send_confirmation(message, response_data)
            else:
                await send_message(message, "Internal error: failed to form response.")
        except Exception as e:
            # Логирование ошибки было бы здесь полезно
            await send_message(message, f"Failed to send response: {e}")

    async def _send_document(self, message: types.Message, file_path: str, caption: str | None):

        if not file_path or not os.path.isfile(file_path):
            await send_message(message, "Internal error: report file not found or path is invalid.")
            return
        
        input_file = FSInputFile(file_path)
        await message.answer_document(input_file, caption=caption)

        try:
            os.remove(file_path)
        except OSError as e:
            # Логирование
            pass

    async def _send_confirmation(self, message: types.Message, response_data: dict):
        """Отправляет сообщение с кнопками 'Да' и 'Нет'."""
        text = response_data.get('text')
        video_id = response_data.get('video_id')

        confirm_button = InlineKeyboardButton(
            text="✅ Да, начать",
            callback_data=VideoCallback(action="start", video_id=video_id).pack()
        )
        cancel_button = InlineKeyboardButton(
            text="❌ Нет, отменить",
            callback_data=VideoCallback(action="cancel", video_id=video_id).pack()
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[confirm_button, cancel_button]])
        
        await message.answer(text, reply_markup=keyboard)