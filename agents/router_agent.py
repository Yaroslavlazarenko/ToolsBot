from typing import TypedDict

from services.gemini_service import GeminiService
from core.schemas import FunctionName, get_routing_schema
from core.enums import GeminiModel

from core.schemas import FUNCTION_DESCRIPTIONS

class RoutingResult(TypedDict):
    text_for_next_step: str
    function_to_call: FunctionName

class RouterAgent:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
        self.routing_schema = get_routing_schema()

    def _create_prompt(self, user_text: str) -> str:

        functions_list = []

        for func_name, description in FUNCTION_DESCRIPTIONS.items():
            functions_list.append(f"- '{func_name}': {description}")
        
        functions_text = "\n".join(functions_list)

        return f"""
        You are an AI-dispatcher. Decide which function to call.


        Available functions:
        {functions_text}

        IMPORTANT: Always instruct the next agent to answer in the same language as the user's request, unless the user explicitly asks for a response in another language. Only switch the response language if the user clearly requests it.

        User request: "{user_text}"
        Your JSON response:
        """

    async def route(self, user_text: str, model: GeminiModel = GeminiModel.GEMINI_2_5_FLASH_LITE) -> RoutingResult | None:
        
        prompt = self._create_prompt(user_text)

        routing_result = await self.gemini_service.generate_json(
            prompt=prompt,
            response_schema=self.routing_schema,
            model=model
        )

        if (isinstance(routing_result, dict) and 
            "error" not in routing_result and
            "function_to_call" in routing_result and
            "text_for_next_step" in routing_result):
            
            try:
                return RoutingResult(
                    text_for_next_step=routing_result["text_for_next_step"],
                    function_to_call=FunctionName(routing_result["function_to_call"])
                )
            except (KeyError, ValueError, TypeError):
                return None
        
        return None