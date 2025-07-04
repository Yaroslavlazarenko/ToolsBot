import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

import telegram.handlers as telHand
from config import Config

async def main():
    config = Config()

    storage = MemoryStorage()
    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dispatcher = Dispatcher(storage=storage)

    dispatcher.include_router(telHand.text.router)

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    await dispatcher.start_polling(bot)


asyncio.run(main())