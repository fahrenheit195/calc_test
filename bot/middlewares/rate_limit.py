from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

import aiosqlite
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from config import config
from db import queries
from services.subscriptions import get_rate_multiplier


class RateLimitMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = data.get("user")
        if not user:
            return await handler(event, data)

        db: aiosqlite.Connection = data["db"]
        tier = user["tier"]
        max_count = config.RATE_LIMIT_MAX * get_rate_multiplier(tier)

        allowed = await queries.check_and_increment_rate_limit(
            db, user["user_id"], config.RATE_LIMIT_WINDOW, max_count
        )
        if not allowed:
            await event.answer(  # type: ignore[attr-defined]
                f"⏳ Слишком много запросов. Подождите немного и попробуйте снова."
            )
            return None

        return await handler(event, data)
