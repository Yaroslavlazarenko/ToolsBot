import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self.bot_token = os.getenv("BOT_TOKEN")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not self.bot_token or not self.gemini_api_key:
            raise ValueError("BOT_TOKEN and GEMINI_API_KEY must be set in the .env file")