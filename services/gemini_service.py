import asyncio
import json
import logging
import time
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
        logger = logging.getLogger("GeminiService")
        max_retries = 5
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt+1}/{max_retries} to generate content for model {model}")
                result = await self.async_client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=genai_config
                )
                logger.info(f"Content generated successfully for model {model}")
                return result
            except Exception as e:
                err_str = str(e)
                logger.error(f"Error during generate_content (attempt {attempt+1}/{max_retries}) for model {model}: {err_str}")
                # Проверка на дневной лимит (сразу, до любых ретраев)
                if (
                    'RESOURCE_EXHAUSTED' in err_str and
                    'GenerateRequestsPerDayPerProjectPerModel-FreeTier' in err_str
                ):
                    logger.critical("Дневной лимит запросов к Gemini API исчерпан. Попробуйте завтра или используйте другую модель/аккаунт.")
                    return {"error": "API_CALL_FAILED", "details": "Дневной лимит запросов к Gemini API исчерпан. Попробуйте завтра или используйте другую модель/аккаунт."}
                # Обработка ошибки 429 (RESOURCE_EXHAUSTED)
                if '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str:
                    limiter_pool = await get_limiter_pool()
                    limiter = limiter_pool.get(model)
                    if limiter and hasattr(limiter, 'requests') and limiter.requests:
                        import time
                        current_time = time.time()
                        first_request_time = limiter.requests[0]
                        window_size = limiter.window_size
                        wait_time = (first_request_time + window_size) - current_time
                        wait_time = max(wait_time, 1)
                        logger.warning(f"429 RESOURCE_EXHAUSTED. Sleeping for {wait_time:.1f} seconds until window opens...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.warning("429 RESOURCE_EXHAUSTED. Limiter not available, sleeping 60s...")
                        await asyncio.sleep(60)
                        continue
                if (
                    '503' in err_str or 'Service Unavailable' in err_str or
                    '500' in err_str or '502' in err_str or
                    'Internal Server Error' in err_str or 'Bad Gateway' in err_str
                ):
                    if attempt < max_retries - 1:
                        logger.warning(f"{err_str}. Retrying after {2 ** attempt} seconds...")
                        await asyncio.sleep(2 ** attempt)
                        continue
                logger.critical(f"API_CALL_FAILED for model {model}: {err_str}")
                return {"error": "API_CALL_FAILED", "details": err_str}

    async def generate_text(self, prompt: str, model: str = GeminiModel.GEMINI_2_5_FLASH, video_part: Optional[Part] = None) -> str:
        logger = logging.getLogger("GeminiService")
        genai_config = GenerateContentConfig(system_instruction=self.system_prompt)
        contents = []
        if video_part:
            contents.append(video_part)
        contents.append(prompt)
        try:
            response = await self._base_generate(contents, model, genai_config)
            if isinstance(response, dict) and "error" in response:
                logger.error(f"Error in generate_text: {response['details']}")
                return f"An error occurred while processing the request: {response['details']}"
            return response.text
        except Exception as e:
            logger.critical(f"Unhandled exception in generate_text: {e}")
            return f"An error occurred while processing the request: {e}"

    async def generate_json(self, prompt: str, response_schema: Schema, model: str = GeminiModel.GEMINI_2_5_FLASH_LITE, video_part: Optional[Part] = None) -> Dict[str, Any]:
        logger = logging.getLogger("GeminiService")
        genai_config = GenerateContentConfig(
            system_instruction=self.system_prompt,
            response_schema=response_schema,
            response_mime_type="application/json"
        )
        contents = []
        if video_part:
            contents.append(video_part)
        contents.append(prompt)
        try:
            response = await self._base_generate(contents, model, genai_config)
            if isinstance(response, dict) and "error" in response:
                logger.error(f"Error in generate_json: {response}")
                return response
            try:
                return json.loads(response.text)
            except (json.JSONDecodeError, TypeError) as decode_err:
                logger.error(f"JSON parse error: {decode_err}. Raw text: {getattr(response, 'text', None)}")
                return {"error": "JSON_PARSE_FAILED", "raw_text": getattr(response, 'text', None)}
        except Exception as e:
            logger.critical(f"Unhandled exception in generate_json: {e}")
            return {"error": "API_CALL_FAILED", "details": str(e)}