import os
from typing import Dict, Union

from agents.router_agent import RouterAgent
from use_cases.function_handler import FunctionHandler


OrchestratorResponse = Dict[str, Union[str, bool]]

class OrchestratorAgent:
    def __init__(self, router_agent: RouterAgent, function_handler: FunctionHandler):
        self.router_agent = router_agent
        self.function_handler = function_handler

    async def process_request(self, user_text: str) -> OrchestratorResponse:
        routing_decision = await self.router_agent.route(user_text)
        if not routing_decision or "function_to_call" not in routing_decision:
            return {'type': 'text', 'content': 'Could not determine the type of your request.'}
        function_name = routing_decision.get("function_to_call")
        text_for_function = routing_decision.get("text_for_next_step")
        if hasattr(self.function_handler, function_name):
            method_to_call = getattr(self.function_handler, function_name)
            final_result = await method_to_call(text_for_function)
            return self._format_response(final_result)
        else:
            return {'type': 'text', 'content': 'Internal error: handler not found.'}

    def _format_response(self, result: str) -> OrchestratorResponse:
        if isinstance(result, str) and os.path.isfile(result):
            return {
                'type': 'document',
                'content': result,
                'caption': 'Your detailed video analysis is ready.'
            }
        else:
            return {
                'type': 'text',
                'content': str(result)
            }