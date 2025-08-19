from aiogram.filters.callback_data import CallbackData

class VideoCallback(CallbackData, prefix="vid"):
    action: str
    video_id: str

# НОВАЯ ФАБРИКА ДЛЯ ОТМЕНЫ
class CancelCallback(CallbackData, prefix="cancel"):
    # Нам нужен уникальный идентификатор задачи, чтобы знать, что отменять.
    # Используем ID чата и ID сообщения с кнопками "Да/Нет".
    chat_id: int
    message_id: int