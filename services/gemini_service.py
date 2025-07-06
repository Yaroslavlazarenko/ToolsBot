from google import genai
from google.genai.types import GenerateContentConfig, Tool
from config import Config
from core.limiter import get_global_gemini_limiter
import asyncio
from typing import List, Optional

class GeminiService:
    def __init__(self, tools: Optional[List[Tool]] = None):
        config = Config()
        self.model_name = config.gemini_model
        self.async_client = genai.Client(api_key=config.gemini_api_key).aio
        self.system_prompt = (
            "You are a helpful assistant..."
        )
        self.tools = tools

    async def generate(self, chat_prompt: List[str]) -> str:
        limiter = await get_global_gemini_limiter()
        while not limiter.allow_request():
            await asyncio.sleep(1)

        # Формируем конфиг с tools, если они есть
        if self.tools:
            genai_config = GenerateContentConfig(
                system_instruction=self.system_prompt,
                tools=self.tools
            )
        else:
            genai_config = GenerateContentConfig(
                system_instruction=self.system_prompt
            )

        try:
            api_response = await self.async_client.models.generate_content(
                model=self.model_name,
                contents=chat_prompt,
                config=genai_config,
            )
            return api_response.text
        except Exception as e:
            print(f"Ошибка вызова Gemini API: {e}")
            return "Произошла ошибка при обработке запроса."