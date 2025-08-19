from google.genai.types import Schema, Type

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