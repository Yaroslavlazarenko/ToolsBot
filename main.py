import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from google import genai

from agents.orchestrator_agent import OrchestratorAgent
from agents.router_agent import RouterAgent
from config import Config
from core.limiter import create_limiter_pool
from services.gemini_service import GeminiService
from telegram.responder import TelegramResponder
from use_cases.function_handler import FunctionHandler
from use_cases.video_processor import VideoProcessor
import telegram.handlers.text as text_handler

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # 1. Конфигурация и клиенты
    config = Config() # pyright: ignore[reportCallIssue]
    file_client = genai.Client(api_key=config.gemini_api_key)
    async_gemini_client = genai.Client(api_key=config.gemini_api_key).aio
    
    # 2. Создание зависимостей (от нижних к верхним)
    limiter_pool = create_limiter_pool()

    gemini_service = GeminiService(
        async_client=async_gemini_client,
        limiter_pool=limiter_pool,
        system_prompt=config.system_prompt,
        max_retries=config.api_max_retries,
    )

    video_processor = VideoProcessor(
        gemini_service=gemini_service,
        file_client=file_client,
        segment_duration=config.video_segment_duration
    )
    
    function_handler = FunctionHandler(
        gemini_service=gemini_service,
        video_processor=video_processor
    )
    
    router_agent = RouterAgent(gemini_service=gemini_service)
    
    orchestrator = OrchestratorAgent(
        router_agent=router_agent,
        function_handler=function_handler
    )
    
    responder = TelegramResponder()

    # 3. Настройка и запуск бота
    storage = MemoryStorage()
    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=None))
    
    dp = Dispatcher(
        storage=storage,
        orchestrator=orchestrator,
        responder=responder
    )
    
    dp.include_router(text_handler.router)
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")