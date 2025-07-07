import asyncio
import json
from typing import List, Any

from google.genai.types import GenerateContentConfig, Schema, Part, GenerateContentResponse

from google.genai.client import AsyncClient
from core.limiter import SlidingWindowLimiter
from core.exceptions import ApiCallFailedError, JsonParseError
from core.enums import GeminiModel

class GeminiService:
    def __init__(
        self,
        async_client: AsyncClient,
        limiter_pool: dict[str, SlidingWindowLimiter],
        system_prompt: str,
        max_retries: int,
    ):
        self.async_client = async_client
        self.limiter_pool = limiter_pool
        self.system_prompt = system_prompt
        self.max_retries = max_retries

    async def _base_generate(self, contents: List[str | Part], model: str, genai_config: GenerateContentConfig) -> GenerateContentResponse:
        
        limiter = self.limiter_pool.get(model)
        if limiter:
            while not limiter.allow_request():
                await asyncio.sleep(1)

        for attempt in range(self.max_retries):
            try:
                # Метод вызывается у .models
                return await self.async_client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=genai_config
                )
            except Exception as e:

                err_str = str(e)
                if '503' in err_str or 'Service Unavailable' in err_str:
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue

                raise ApiCallFailedError(details=err_str)
        
        raise ApiCallFailedError(details="Max retries exceeded")

    async def generate_text(self, prompt: str, model: str = GeminiModel.GEMINI_2_5_FLASH, video_part: Part | None = None) -> str:
        genai_config = GenerateContentConfig(system_instruction=self.system_prompt)
        
        contents: List[str | Part]

        if video_part:
            contents = [video_part, prompt]
        else:
            contents = [prompt]
        
        try:
            response = await self._base_generate(contents, model, genai_config)
            return response.text or ""
        except ApiCallFailedError as e:
            return f"An error occurred while processing the request: {e.details}"

    async def generate_json(self, prompt: str, response_schema: Schema, model: str = GeminiModel.GEMINI_2_5_FLASH_LITE, video_part: Part | None = None) -> dict[str, Any]:
        genai_config = GenerateContentConfig(
            system_instruction=self.system_prompt,
            response_schema=response_schema,
            response_mime_type="application/json"
        )

        contents: List[str | Part]

        if video_part:
            contents = [video_part, prompt]
        else:
            contents = [prompt]

        response = await self._base_generate(contents, model, genai_config)

        if not response.text:
            raise JsonParseError("API response is empty", raw_text=None)
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            raise JsonParseError("Failed to decode JSON from API response", raw_text=response.text)