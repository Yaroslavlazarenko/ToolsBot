from google import genai

from config import Config


config = Config()

client = genai.Client(api_key=config.gemini_api_key)
async_client = client.aio

system_prompt = (
    "You are a helpful assistant. "
    "You will answer questions and provide information based on the provided contents."
)

api_response = await async_client.models._generate_content(
    model=config.gemini_model,
    contents=chat_contents,
    config=GenerateContentConfig(
        response_modalities=["text"],
        system_instruction=system_prompt,
    ),
)