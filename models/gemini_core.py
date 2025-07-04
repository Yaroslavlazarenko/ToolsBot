from google import genai
from google.genai.types import GenerateContentConfig
from config import Config

config = Config()

client = genai.Client(api_key=config.gemini_api_key)
async_client = client.aio

system_prompt = (
    "You are a helpful assistant. "
    "You will answer questions and provide information based on the provided contents."
    "Don't use text formatting in your responses."
    )

async def generate_content(prompt: str) -> str:
    """Базовая функция для генерации контента без инструментов."""
    api_response = await async_client.models.generate_content(
        model=config.gemini_model,
        contents=[prompt],
        config=GenerateContentConfig(
            system_instruction=system_prompt
        ),
    )
    return api_response.text