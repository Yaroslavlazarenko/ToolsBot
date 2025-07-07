from google.genai.types import Schema, Type

def get_routing_schema() -> Schema:
    return Schema(
        type=Type.OBJECT,
        properties={
            'text_for_next_step': Schema(
                type=Type.STRING,
                description="A clear instruction for the next agent: reformulate the user's request as a direct instruction, including all necessary context and requirements. The next agent will treat this as an explicit instruction to follow."
            ),
            'function_to_call': Schema(
                type=Type.STRING,
                description="Name of the function to call: 'analyze_video_content', 'get_hard_text_response', or 'get_light_text_response'."
            )
        },
        required=['text_for_next_step', 'function_to_call']
    )