import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from pyrogram import Client as PyrogramClient
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_API_ID, TELEGRAM_API_HASH
from handlers import register, upload, profile

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Pyrogram клиент для скачивания файлов через MTProto (лимит 2GB вместо 20MB)
pyrogram_client = PyrogramClient(
    "beethoven_bot",
    api_id=TELEGRAM_API_ID,
    api_hash=TELEGRAM_API_HASH,
    bot_token=TELEGRAM_BOT_TOKEN,
    workdir=".",
    no_updates=True,
)

dp.include_router(register.router)
dp.include_router(upload.router)
dp.include_router(profile.router)


async def main():
    await pyrogram_client.start()
    logging.info("Pyrogram client started")

    # Пробрасываем в хендлеры через aiogram DI
    dp["pyrogram_client"] = pyrogram_client

    try:
        await dp.start_polling(bot)
    finally:
        await pyrogram_client.stop()
        logging.info("Pyrogram client stopped")


if __name__ == "__main__":
    asyncio.run(main())
