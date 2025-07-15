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

# --- Функции для управления вебхуками ---
async def on_startup_webhook(dispatcher: Dispatcher, bot: Bot, config: Config):
    logging.info("Устанавливаем вебхук в Telegram...")
    webhook_url = f"{config.WEBHOOK_HOST}{config.WEBHOOK_PATH}"
    logging.info(f"URL вебхука для установки: {webhook_url}")

    try:
        await bot.set_webhook(webhook_url)
        logging.info(f"Вебхук установлен успешно на: {webhook_url}")
    except Exception as e:
        logging.error(f"Ошибка при установке вебхука: {e}", exc_info=True)

    try:
        webhook_info = await bot.get_webhook_info()
        logging.info(f"Информация о вебхуке после попытки установки: {webhook_info}")
    except Exception as e:
        logging.error(f"Ошибка при получении информации о вебхуке: {e}", exc_info=True)


async def on_shutdown_webhook(dispatcher: Dispatcher, bot: Bot):
    logging.info("Удаляем вебхук из Telegram...")
    try:
        await bot.delete_webhook()
        logging.info("Вебхук удален успешно.")
    except Exception as e:
        logging.error(f"Ошибка при удалении вебхука: {e}", exc_info=True)
    
    try:
        webhook_info = await bot.get_webhook_info()
        logging.info(f"Информация о вебхуке после удаления: {webhook_info}")
    except Exception as e:
        logging.error(f"Ошибка при получении информации о вебхуке после удаления: {e}", exc_info=True)

# --- Основная функция запуска бота ---
def main(): # Синхронная функция
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    config = Config() # type: ignore
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

    app = web.Application()

    # <--- ГЛАВНЫЕ ИЗМЕНЕНИЯ ЗДЕСЬ
    # Регистрируем SimpleRequestHandler для обработки вебхуков
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=None
    )
    webhook_requests_handler.register(app, path=config.WEBHOOK_PATH)

    # Запускаем on_startup_webhook как отдельную задачу перед запуском веб-приложения
    # Это гарантирует, что bot.set_webhook() будет вызван.
    async def start_webhook_task():
        await on_startup_webhook(dp, bot, config)

    # Регистрируем эту задачу для выполнения при старте aiohttp приложения
    app.on_startup.append(lambda _: asyncio.create_task(start_webhook_task()))

    # Регистрируем on_shutdown_webhook для выполнения при остановке aiohttp приложения
    app.on_shutdown.append(lambda _: on_shutdown_webhook(dp, bot))
    # ---> КОНЕЦ ГЛАВНЫХ ИЗМЕНЕНИЙ

    logging.info(f"Запускаем aiohttp веб-сервер на {config.WEBAPP_HOST}:{config.WEBAPP_PORT}...")
    web.run_app(
        app,
        host=config.WEBAPP_HOST,
        port=config.WEBAPP_PORT,
    )
    
    logging.info("Бот остановлен.")

if __name__ == '__main__':
    try:
        main() 
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped by user or system signal.")