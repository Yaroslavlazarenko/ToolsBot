from google.genai.types import Schema, Type

def get_routing_schema() -> Schema:
    return Schema(
        type=Type.OBJECT,
        properties={
            'text_for_next_step': Schema(
                type=Type.STRING,
                description="Original or slightly reformulated request for the next step."
            ),
            'function_to_call': Schema(
                type=Type.STRING,
                description="Name of the function to call: 'analyze_video_content' or 'get_text_response'."
            )
        },
        required=['text_for_next_step', 'function_to_call']
    )