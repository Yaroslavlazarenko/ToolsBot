
from enum import Enum

class GeminiModel(str, Enum):
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite-preview-06-17"

class RateLimits(int, Enum):
    RATE_LIMIT_2_5_FLASH=11
    RATE_LIMIT_2_5_FLASH_LITE=16
    RATE_LIMIT_2_5_PRO=6
    
    RATE_LIMIT_WINDOW=60
