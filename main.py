import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from agents.router_agent import RouterAgent
from agents.orchestrator_agent import OrchestratorAgent
from services.gemini_service import GeminiService
import telegram.handlers as telHand
from config import Config
from use_cases.function_handler import FunctionHandler
from telegram.responder import TelegramResponder

async def main():
    config = Config() # pyright: ignore[reportCallIssue]

    gemini_service = GeminiService()
    router_agent = RouterAgent(gemini_service=gemini_service)
    function_handler = FunctionHandler(gemini_service=gemini_service)

    orchestrator = OrchestratorAgent(
        router_agent=router_agent,
        function_handler=function_handler
    )

    responder = TelegramResponder()

    storage = MemoryStorage()
    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=None))

    dispatcher = Dispatcher(
        storage=storage,
        orchestrator=orchestrator,
        responder=responder
    )

    dispatcher.include_router(telHand.text.router)

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    await dispatcher.start_polling(bot)


asyncio.run(main())