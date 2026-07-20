from __future__ import annotations

from typing import Any, Awaitable, Callable

import aiosqlite
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from config import config
from db import queries
from services.subscriptions import get_rate_multiplier


class RateLimitMiddleware(BaseMiddleware):
    """Registered on dp.message, so `event` is a Message."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("user")
        if not isinstance(event, Message) or not user:
            return await handler(event, data)

        # Payment confirmations and admins are never throttled
        if event.successful_payment or user["user_id"] in config.ADMIN_IDS:
            return await handler(event, data)

        db: aiosqlite.Connection = data["db"]
        max_count = config.RATE_LIMIT_MAX * get_rate_multiplier(user["tier"])

        allowed = await queries.check_and_increment_rate_limit(
            db, user["user_id"], config.RATE_LIMIT_WINDOW, max_count
        )
        if not allowed:
            await event.answer(
                "⏳ Слишком много запросов. Подождите немного и попробуйте снова."
            )
            return None

        return await handler(event, data)
