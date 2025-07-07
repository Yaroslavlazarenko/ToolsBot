      
class ServiceError(Exception):
    """Базовое исключение для всех ошибок сервисного слоя."""
    pass

class ApiCallFailedError(ServiceError):
    """Выбрасывается, когда API-запрос провалился после всех попыток."""
    def __init__(self, details: str):
        self.details = details
        super().__init__(f"API call failed: {details}")

class JsonParseError(ServiceError):
    """Выбрасывается, когда не удалось распарсить JSON из ответа API."""
    def __init__(self, message: str, raw_text: str | None = None):
        self.raw_text = raw_text
        super().__init__(f"{message}. Raw text: {raw_text[:200] if raw_text else 'N/A'}")

class VideoProcessingError(ServiceError):
    """Выбрасывается при ошибках скачивания или обработки видео."""
    pass

    