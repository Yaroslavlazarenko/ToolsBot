from services.gemini_service import GeminiService
from core.enums import GeminiModel
from use_cases.video_processor import VideoProcessor
from core.exceptions import VideoProcessingError

class FunctionHandler:
    def __init__(self, gemini_service: GeminiService, video_processor: VideoProcessor):
        self.gemini_service = gemini_service
        self.video_processor = video_processor

    async def get_hard_text_response(self, text_from_router: str) -> str:
        return await self.gemini_service.generate_text(
            prompt=text_from_router,
            model=GeminiModel.GEMINI_2_5_PRO
        )
    
    async def get_light_text_response(self, text_from_router: str) -> str:
        return await self.gemini_service.generate_text(
            prompt=text_from_router,
            model=GeminiModel.GEMINI_2_5_FLASH_LITE
        )

    async def analyze_video_content(self, text_from_router: str) -> str:
        try:
            return await self.video_processor.analyze_video_from_prompt(text_from_router)
        except VideoProcessingError as e:
            return str(e)