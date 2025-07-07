import asyncio
import json
from typing import List, Any

from google.genai import Client
from google.genai.types import GenerateContentConfig, Schema, Part, GenerateContentResponse

from typing import TypedDict, Literal

from config import Config
from core.limiter import get_limiter_pool
from core.enums import GeminiModel

class ApiErrorDict(TypedDict):
    error: Literal["API_CALL_FAILED"]
    details: str

class JsonParseErrorDict(TypedDict):
    error: Literal["JSON_PARSE_FAILED"]
    raw_text: str | None

class GeminiService:
    def __init__(self):
        config = Config() # pyright: ignore[reportCallIssue]
        self.async_client = Client(api_key=config.gemini_api_key).aio
        self.system_prompt = "You are a helpful and efficient AI assistant. Don't use markdown formatting in your responses, just plain text. Always respond in the same language as the user's request, unless explicitly asked to switch languages."

    async def _base_generate(self, contents: List[str | Part], model: str, genai_config: GenerateContentConfig) -> GenerateContentResponse | dict[str, str]:
        
        limiter_pool = await get_limiter_pool()
        limiter = limiter_pool.get(model)

        if limiter:
            while not limiter.allow_request():
                await asyncio.sleep(1)

        max_retries = 3

        for attempt in range(max_retries):

            try:
                return await self.async_client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=genai_config
                )
            except Exception as e:
                err_str = str(e)

                if '503' in err_str or 'Service Unavailable' in err_str:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue

                return {"error": "API_CALL_FAILED", "details": err_str}
            
        return {"error": "API_CALL_FAILED", "details": "Max retries exceeded"}

    async def generate_text(self, prompt: str, model: str = GeminiModel.GEMINI_2_5_FLASH, video_part: Part | None = None) -> str:
        genai_config = GenerateContentConfig(system_instruction=self.system_prompt)
        contents = []

        if video_part:
            contents.append(video_part)

        contents.append(prompt)
        response = await self._base_generate(contents, model, genai_config)

        if isinstance(response, dict):
            return f"An error occurred while processing the request: {response.get('details', 'Unknown error')}"
        
        return response.text or ""

    async def generate_json(
            self, 
            prompt: str, 
            response_schema: Schema, 
            model: str = GeminiModel.GEMINI_2_5_FLASH_LITE, 
            video_part: Part | None = None
        ) -> dict[str, Any] | ApiErrorDict | JsonParseErrorDict:
        
        genai_config = GenerateContentConfig(
            system_instruction=self.system_prompt,
            response_schema=response_schema,
            response_mime_type="application/json"
        )

        contents: List[str | Part] = []
        if video_part:
            contents.append(video_part)
        contents.append(prompt)

        response = await self._base_generate(contents, model, genai_config)

        if isinstance(response, dict):
            return response
        
        if response.text is None:
            return {"error": "JSON_PARSE_FAILED", "raw_text": None}

        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {"error": "JSON_PARSE_FAILED", "raw_text": response.text}