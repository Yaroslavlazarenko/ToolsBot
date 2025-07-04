from google import genai
from google.genai.types import GenerateContentConfig

from config import Config


config = Config()

client = genai.Client(api_key=config.gemini_api_key)
async_client = client.aio

system_prompt = (
    "You are a helpful assistant. "
    "You will answer questions and provide information based on the provided contents."
)

def multiply(a: float, b: float) -> float:
    """
    Returns the product of two numbers.
    """
    print(f"[Вызов функции: multiply(a={a}, b={b})]")
    return a * b

async def generate_content(chat_prompt: list[str]) -> str:
    api_response = await async_client.models.generate_content(
            model=config.gemini_model,
            contents=chat_prompt,
            config=GenerateContentConfig(
                tools=[multiply],
                system_instruction=system_prompt
            ),
        )
    return api_response.text