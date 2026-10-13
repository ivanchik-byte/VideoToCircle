import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode

from config import settings
from handlers import router
from storage import init_db


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Initialize user preferences storage
    init_db()

    if not settings.bot_token:
        logging.error("BOT_TOKEN is not set. Please provide it in .env or environment variables.")
        sys.exit(1)

    session = None
    if settings.local_bot_api_url:
        logging.info(f"Using local Telegram Bot API server at {settings.local_bot_api_url}")
        api_server = TelegramAPIServer.from_base(
            base=settings.local_bot_api_url,
            is_local=settings.local_bot_api_is_local,
        )
        session = AiohttpSession(api=api_server)

    bot = None
    try:
        bot = Bot(
            token=settings.bot_token,
            session=session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dispatcher = Dispatcher()
        dispatcher.include_router(router)

        logging.info("Starting VideoToCircle bot polling...")
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        if bot and bot.session:
            await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
