import asyncio
import json
import logging
from typing import List, Optional, Union, Any, Dict

from google.genai import Client
from google.genai.types import GenerateContentConfig, Schema, Part
from config import Config
from core.enums import GeminiModel

class GeminiService:
    def __init__(self):
        # Возвращаем простую инициализацию, которая работает
        config = Config()
        self.async_client = Client(api_key=config.gemini_api_key).aio
        self.system_prompt = "You are a helpful and efficient AI assistant. Don't use markdown formatting. Respond in the same language as the user's request."
        self.logger = logging.getLogger("GeminiService")

    async def _base_generate(self, contents: List[Union[str, Part]], model: str, genai_config: GenerateContentConfig) -> Any:
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempt {attempt+1}/{max_retries} to generate content for model {model}")
                result = await self.async_client.models.generate_content(
                    model=model, contents=contents, config=genai_config
                )
                self.logger.info(f"Content generated successfully for model {model}")
                return result
            except Exception as e:
                err_str = str(e)
                self.logger.error(f"Error on attempt {attempt+1}: {err_str}")
                if 'RESOURCE_EXHAUSTED' in err_str:
                    if 'PerDay' in err_str:
                        self.logger.critical("Daily API limit exhausted.")
                        return {"error": "API_LIMIT_EXHAUSTED", "details": "Дневной лимит запросов к Gemini API исчерпан."}
                    self.logger.warning("Rate limit hit (429). Sleeping for 60s...")
                    await asyncio.sleep(60)
                    continue
                
                if '50' in err_str: # Catches 500, 502, 503 server errors
                    if attempt < max_retries - 1:
                        sleep_time = 2 ** attempt
                        self.logger.warning(f"Server error. Retrying after {sleep_time} seconds...")
                        await asyncio.sleep(sleep_time)
                        continue

                self.logger.critical(f"API call failed for model {model} after all retries: {err_str}")
                return {"error": "API_CALL_FAILED", "details": err_str}

    async def generate_text(self, prompt: str, model: str = GeminiModel.GEMINI_2_5_FLASH, video_part: Optional[Part] = None) -> str:
        genai_config = GenerateContentConfig(system_instruction=self.system_prompt)
        contents = [video_part, prompt] if video_part else [prompt]
        
        response = await self._base_generate(contents, model, genai_config)
        if isinstance(response, dict) and "error" in response:
            return f"An error occurred: {response['details']}"
        return response.text

    async def generate_json(self, prompt: str, response_schema: Schema, model: str = GeminiModel.GEMINI_2_5_FLASH_LITE) -> Dict[str, Any]:
        genai_config = GenerateContentConfig(
            system_instruction=self.system_prompt,
            response_schema=response_schema,
            response_mime_type="application/json"
        )
        response = await self._base_generate([prompt], model, genai_config)
        if isinstance(response, dict) and "error" in response:
            return response
        try:
            return json.loads(response.text)
        except (json.JSONDecodeError, TypeError):
            self.logger.error(f"JSON parse error. Raw text: {getattr(response, 'text', None)}")
            return {"error": "JSON_PARSE_FAILED", "raw_text": getattr(response, 'text', None)}