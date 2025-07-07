from typing import TypedDict
from services.gemini_service import GeminiService
from core.schemas import FunctionName, get_routing_schema
from core.enums import GeminiModel
from core.schemas import FUNCTION_DESCRIPTIONS
from core.exceptions import ServiceError

class RoutingResult(TypedDict):
    text_for_next_step: str
    function_to_call: FunctionName

class RouterAgent:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
        self.routing_schema = get_routing_schema()

    def _create_prompt(self, user_text: str) -> str:
        functions_list = [f"- '{name}': {desc}" for name, desc in FUNCTION_DESCRIPTIONS.items()]
        functions_text = "\n".join(functions_list)
        return (
            "You are an AI-dispatcher. Decide which function to call based on the user's request.\n"
            "Available functions:\n"
            f"{functions_text}\n"
            "IMPORTANT: Always instruct the next agent to answer in the same language as the user's request.\n"
            f'User request: "{user_text}"\n'
            "Your JSON response:"
        )

    async def route(self, user_text: str, model: GeminiModel = GeminiModel.GEMINI_2_5_FLASH_LITE) -> RoutingResult | None:
        prompt = self._create_prompt(user_text)
        try:
            routing_result = await self.gemini_service.generate_json(
                prompt=prompt,
                response_schema=self.routing_schema,
                model=model
            )
            return RoutingResult(
                text_for_next_step=routing_result["text_for_next_step"],
                function_to_call=FunctionName(routing_result["function_to_call"])
            )
        except (ServiceError, KeyError, ValueError, TypeError):
            # Логируем ошибку, если нужно, но для пользователя возвращаем None
            return None