from typing import Dict, Any, Optional

from services.gemini_service import GeminiService
from core.schemas import get_routing_schema
from core.enums import GeminiModel

class RouterAgent:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
        self.routing_schema = get_routing_schema()
        self.model = GeminiModel.GEMINI_2_5_FLASH_LITE

    def _create_prompt(self, user_text: str) -> str:
        return f"""
        You are an AI-dispatcher. Decide which function to call.

        Available functions:
        - 'analyze_video_content': Call if the request contains a YouTube link (youtube.com or youtu.be) and asks for video analysis.
        - 'get_text_response': Call for all other cases — general questions, simple dialog, requests to generate something, and for SHORT video summaries (that can be made from subtitles).

        IMPORTANT: Always instruct the next agent to answer in the same language as the user's request, unless the user explicitly asks for a response in another language. Only switch the response language if the user clearly requests it.

        User request: "{user_text}"
        Your JSON response:
        """

    async def route(self, user_text: str) -> Optional[Dict[str, Any]]:
        prompt = self._create_prompt(user_text)
        routing_result = await self.gemini_service.generate_json(
            prompt=prompt,
            response_schema=self.routing_schema,
            model=self.model
        )
        if isinstance(routing_result, dict) and "error" not in routing_result:
            return routing_result
        else:
            return None