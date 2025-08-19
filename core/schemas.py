from google.genai.types import Schema, Type

from .enums import FunctionName

FUNCTION_DESCRIPTIONS = {
    FunctionName.ANALYZE_VIDEO_CONTENT: (
        "Analyzes the content of a YouTube video based on a user's request. "
        "This function requires the full user prompt containing the YouTube link (e.g., youtube.com, youtu.be) "
        "and the specific analysis instructions. The prompt should be passed as the 'user_prompt' argument."
    ),
    
    FunctionName.GET_HARD_TEXT_RESPONSE: (
        "Responds to a user's request that requires a detailed, deep, or complex answer. "
        "Use this for tasks needing strong reasoning or in-depth explanations. "
        "The function requires the full user's request text to be passed as the 'user_prompt' argument."
    ),
    
    FunctionName.GET_LIGHT_TEXT_RESPONSE: (
        "Responds to a simple or short user's request that can be answered briefly. "
        "Use this for casual chat, short facts, or when a fast response is preferred. "
        "The function requires the full user's request text to be passed as the 'user_prompt' argument."
    )
}

def get_routing_schema() -> Schema:

    return Schema(
        type=Type.OBJECT,
        properties={
            'function_to_call': Schema(
                type=Type.STRING,
                description="Name of the function to call: 'analyze_video_content', 'get_hard_text_response', or 'get_light_text_response'."
            ),
            'language': Schema(
                type=Type.STRING,
                description="The detected language of the user's request (e.g., 'Russian', 'English')."
            )
        },
        # 'text_for_next_step' больше не требуется
        required=['function_to_call', 'language']
    )