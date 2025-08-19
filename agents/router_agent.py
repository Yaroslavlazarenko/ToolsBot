import logging
from typing import Dict, Any, Optional
from services.gemini_service import GeminiService
from core.schemas import get_routing_schema
from core.enums import GeminiModel

class RouterAgent:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
        self.routing_schema = get_routing_schema()
        self.model = GeminiModel.GEMINI_2_5_FLASH_LITE
        self.logger = logging.getLogger("RouterAgent")

    def _create_prompt(self, user_text: str) -> str:
        return f"""
        You are an AI-dispatcher. Your tasks are to determine the correct function to call and the language of the user's request.
        Your response MUST be ONLY a valid JSON object. Do not add any explanatory text.

        Available functions:
        - 'analyze_video_content': If the request contains a YouTube link.
        - 'get_hard_text_response': For complex questions.
        - 'get_light_text_response': For simple questions.
        
        User request: "{user_text}"
        """

    async def route(self, user_text: str) -> Optional[Dict[str, Any]]:
        prompt = self._create_prompt(user_text)
        routing_result = await self.gemini_service.generate_json(prompt=prompt, response_schema=self.routing_schema, model=self.model)
        if isinstance(routing_result, dict) and "error" not in routing_result:
            self.logger.info(f"Routing successful: {routing_result}")
            return routing_result
        else:
            self.logger.error(f"Routing failed. Raw result from Gemini: {routing_result}")
            return None