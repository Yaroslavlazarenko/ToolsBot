from google.genai.types import Schema, Type

from enum import StrEnum

class FunctionName(StrEnum):
    ANALYZE_VIDEO_CONTENT = "analyze_video_content"
    GET_HARD_TEXT_RESPONSE = "get_hard_text_response"
    GET_LIGHT_TEXT_RESPONSE = "get_light_text_response"

FUNCTION_DESCRIPTIONS = {
    FunctionName.ANALYZE_VIDEO_CONTENT: "Call if the request contains a YouTube link (youtube.com or youtu.be) and asks for video analysis.",
    FunctionName.GET_HARD_TEXT_RESPONSE: "Call if the user's request requires a detailed, deep, or complex answer, or if the user explicitly asks for a thorough or advanced response. Use this for tasks that need strong reasoning, multi-step logic, or in-depth explanations.",
    FunctionName.GET_LIGHT_TEXT_RESPONSE: "Call if the user's request is simple, short, or can be answered briefly, or if the user explicitly asks for a quick, lightweight, or basic answer. Use this for casual chat, short facts, or when a fast response is preferred over depth."
}

def get_routing_schema() -> Schema:

    return Schema(
        type=Type.OBJECT,
        properties={
            'text_for_next_step': Schema(
                type=Type.STRING,
                description="A clear instruction for the next agent: reformulate the user's " \
                "request as a direct instruction, including all necessary context and requirements. " \
                "The next agent will treat this as an explicit instruction to follow."
            ),
            'function_to_call': Schema(
                type=Type.STRING,
                format="enum",
                enum=[name.value for name in FunctionName],
                description="Name of the function to call."
            )
        },
        required=['text_for_next_step', 'function_to_call']
    )