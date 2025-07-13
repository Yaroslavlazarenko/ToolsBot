import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web 

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
    
    config = Config() # pyright: ignore[reportCallIssue]
    file_client = genai.Client(api_key=config.gemini_api_key)
    async_gemini_client = genai.Client(api_key=config.gemini_api_key).aio
    
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

    storage = MemoryStorage()
    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=None))
    
    dp = Dispatcher(
        storage=storage,
        orchestrator=orchestrator,
        responder=responder
    )
    
    dp.include_router(text_handler.router)

    async def on_startup_webhook(dispatcher: Dispatcher, bot: Bot, config: Config):
        logging.info("Устанавливаем вебхук в Telegram...")
        webhook_url = f"{config.WEBHOOK_HOST}{config.WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url)
        logging.info(f"Вебхук установлен на: {webhook_url}")
        webhook_info = await bot.get_webhook_info()
        logging.info(f"Информация о вебхуке: {webhook_info}")

    async def on_shutdown_webhook(dispatcher: Dispatcher, bot: Bot):
        logging.info("Удаляем вебхук из Telegram...")
        await bot.delete_webhook()
        logging.info("Вебхук удален.")
        webhook_info = await bot.get_webhook_info()
        logging.info(f"Информация о вебхуке после удаления: {webhook_info}")

    dp.startup.register(lambda: on_startup_webhook(dp, bot, config))
    dp.shutdown.register(lambda: on_shutdown_webhook(dp, bot))

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=None
    )

    webhook_requests_handler.register(app, path=config.WEBHOOK_PATH) 

    logging.info(f"Запускаем aiohttp веб-сервер на {config.WEBAPP_HOST}:{config.WEBAPP_PORT}...")
    web.run_app(
        app,
        host=config.WEBAPP_HOST,
        port=config.WEBAPP_PORT,
    )
    
    logging.info("Бот остановлен.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped by user or system signal.")


