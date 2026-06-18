from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from db.connection import create_connection, ensure_schema, set_db_path
from handlers import admin, generate, payments, start, tos
from middlewares.rate_limit import RateLimitMiddleware
from middlewares.tos_gate import ToSGateMiddleware
from middlewares.user_loader import UserLoaderMiddleware
from services.image_backend import get_backend

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    set_db_path(config.DB_PATH)
    db = await create_connection()
    await ensure_schema(db)
    logger.info("Database initialized at %s", config.DB_PATH)

    image_backend = get_backend(config)
    logger.info("Image backend: %s", image_backend.__class__.__name__)

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp["db"] = db
    dp["image_backend"] = image_backend

    dp.update.middleware(UserLoaderMiddleware())
    dp.update.middleware(RateLimitMiddleware())
    dp.update.middleware(ToSGateMiddleware())

    dp.include_router(tos.router)
    dp.include_router(start.router)
    dp.include_router(generate.router)
    dp.include_router(payments.router)
    dp.include_router(admin.router)

    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.close()
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
