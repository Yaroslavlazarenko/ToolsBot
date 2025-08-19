import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage  # Убедитесь, что это импортировано

from agents.router_agent import RouterAgent
from agents.orchestrator_agent import OrchestratorAgent
from services.gemini_service import GeminiService
from use_cases.function_handler import FunctionHandler
from telegram.responder import TelegramResponder
from config import Config
from core.task_manager import task_manager
from core.analysis_manager import analysis_manager

import telegram.handlers.text as text_handler
import telegram.handlers.callbacks as callback_handler

async def main():
    config = Config()
    
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 1. Создаем хранилище
    storage = MemoryStorage()
    
    # 2. Инициализация всех компонентов
    gemini_service = GeminiService()
    router_agent = RouterAgent(gemini_service=gemini_service)
    function_handler = FunctionHandler(gemini_service=gemini_service)
    responder = TelegramResponder()
    
    orchestrator = OrchestratorAgent(
        router_agent=router_agent,
        function_handler=function_handler,
        responder=responder
    )
    
    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=None))

    # 3. ПЕРЕДАЕМ ХРАНИЛИЩЕ В ДИСПЕТЧЕР. ЭТО КЛЮЧЕВОЙ МОМЕНТ!
    dispatcher = Dispatcher(
        storage=storage,
        orchestrator=orchestrator,
        responder=responder,
        task_manager=task_manager,
        analysis_manager=analysis_manager # Передаем для порядка
    )

    dispatcher.include_router(text_handler.router)
    dispatcher.include_router(callback_handler.router)

    logging.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")