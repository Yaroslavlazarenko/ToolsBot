from aiogram.filters.callback_data import CallbackData

class VideoCallback(CallbackData, prefix="vid"):
    """
    Данные для кнопок подтверждения (Да/Нет).
    """
    action: str  # 'start' или 'cancel'
    video_id: str

class CancelCallback(CallbackData, prefix="cancel"):
    """
    Данные для кнопки отмены уже запущенного процесса.
    """
    chat_id: int
    message_id: int