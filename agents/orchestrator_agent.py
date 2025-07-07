import os
from agents.router_agent import RouterAgent
from use_cases.function_handler import FunctionHandler
from core.enums import FunctionName

OrchestratorResponse = dict[str, str | bool]

class OrchestratorAgent:
    def __init__(self, router_agent: RouterAgent, function_handler: FunctionHandler):
        self.router_agent = router_agent
        
        self.dispatch_map = {
            FunctionName.ANALYZE_VIDEO_CONTENT: function_handler.analyze_video_content,
            FunctionName.GET_HARD_TEXT_RESPONSE: function_handler.get_hard_text_response,
            FunctionName.GET_LIGHT_TEXT_RESPONSE: function_handler.get_light_text_response,
        }

    async def process_request(self, user_text: str) -> OrchestratorResponse:
        routing_decision = await self.router_agent.route(user_text)

        if not routing_decision:
            return {'type': 'text', 'content': 'Could not determine how to handle your request.'}
        
        function_to_call = routing_decision["function_to_call"]
        text_for_function = routing_decision["text_for_next_step"]
        
        handler_method = self.dispatch_map.get(function_to_call)
        
        if handler_method:
            final_result = await handler_method(text_for_function)
            return self._format_response(final_result)
        else:
            return {'type': 'text', 'content': f'Internal error: handler for {function_to_call} not found.'}

    def _format_response(self, result: str) -> OrchestratorResponse:
        if isinstance(result, str) and os.path.isfile(result):
            return {'type': 'document', 'content': result, 'caption': 'Your detailed video analysis is ready.'}
        else:
            return {'type': 'text', 'content': str(result)}