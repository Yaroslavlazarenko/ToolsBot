from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    gemini_api_key: str
    
    # Промпт по умолчанию для Gemini
    system_prompt: str = (
        "You are a helpful and efficient AI assistant. "
        "Don't use markdown formatting in your responses, just plain text. "
        "Always respond in the same language as the user's request, "
        "unless explicitly asked to switch languages."
    )

    # Настройки для обработки видео
    video_segment_duration: int = 600  # 10 минут

    # Настройки API
    api_max_retries: int = 3