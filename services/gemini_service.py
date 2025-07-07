import asyncio
import json
from typing import List, Optional, Union, Any, Dict

from google.genai import Client
from google.genai.types import GenerateContentConfig, Schema, Part

from config import Config
from core.limiter import get_limiter_pool
from core.enums import GeminiModel

class GeminiService:
    def __init__(self):
        config = Config()
        self.async_client = Client(api_key=config.gemini_api_key).aio
        self.system_prompt = "You are a helpful and efficient AI assistant. Don't use markdown formatting in your responses, just plain text. Always respond in the same language as the user's request, unless explicitly asked to switch languages."

    async def _base_generate(self, contents: List[Union[str, Part]], model: str, genai_config: GenerateContentConfig) -> Any:
        limiter_pool = await get_limiter_pool()
        limiter = limiter_pool.get(model)
        if limiter:
            while not limiter.allow_request():
                await asyncio.sleep(1)
        else:
            pass
        try:
            return await self.async_client.models.generate_content(
                model=model,
                contents=contents,
                config=genai_config
            )
        except Exception as e:
            return {"error": "API_CALL_FAILED", "details": str(e)}

    async def generate_text(self, prompt: str, model: str = GeminiModel.GEMINI_2_5_FLASH, video_part: Optional[Part] = None) -> str:
        genai_config = GenerateContentConfig(system_instruction=self.system_prompt)
        contents = []
        if video_part:
            contents.append(video_part)
        contents.append(prompt)
        response = await self._base_generate(contents, model, genai_config)
        if isinstance(response, dict) and "error" in response:
            return f"An error occurred while processing the request: {response['details']}"
        return response.text

    async def generate_json(self, prompt: str, response_schema: Schema, model: str = GeminiModel.GEMINI_2_5_FLASH_LITE, video_part: Optional[Part] = None) -> Dict[str, Any]:
        genai_config = GenerateContentConfig(
            system_instruction=self.system_prompt,
            response_schema=response_schema,
            response_mime_type="application/json"
        )
        contents = []
        if video_part:
            contents.append(video_part)
        contents.append(prompt)
        response = await self._base_generate(contents, model, genai_config)
        if isinstance(response, dict) and "error" in response:
            return response
        try:
            return json.loads(response.text)
        except (json.JSONDecodeError, TypeError):
            return {"error": "JSON_PARSE_FAILED", "raw_text": response.text}