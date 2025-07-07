
from enum import IntEnum, StrEnum

class GeminiModel(StrEnum):
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite-preview-06-17"

class RateLimits(IntEnum):
    RATE_LIMIT_2_5_FLASH=11
    RATE_LIMIT_2_5_FLASH_LITE=16
    RATE_LIMIT_2_5_PRO=6
    
    RATE_LIMIT_WINDOW=60

MODEL_TO_RATE_LIMIT_MAP: dict[GeminiModel, RateLimits] = {
    GeminiModel.GEMINI_2_5_PRO: RateLimits.RATE_LIMIT_2_5_PRO,
    GeminiModel.GEMINI_2_5_FLASH: RateLimits.RATE_LIMIT_2_5_FLASH,
    GeminiModel.GEMINI_2_5_FLASH_LITE: RateLimits.RATE_LIMIT_2_5_FLASH_LITE,
}


