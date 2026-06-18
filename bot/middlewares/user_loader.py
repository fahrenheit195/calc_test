from __future__ import annotations

from typing import Any, Awaitable, Callable

import aiosqlite
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from db import queries


class UserLoaderMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        db: aiosqlite.Connection = data["db"]

        from_user = None
        update: Update = data.get("event_update") or data.get("update")  # type: ignore[assignment]
        if update:
            for attr in ("message", "callback_query", "pre_checkout_query"):
                obj = getattr(update, attr, None)
                if obj and getattr(obj, "from_user", None):
                    from_user = obj.from_user
                    break

        if from_user:
            user = await queries.get_or_create_user(db, from_user.id, from_user.username)
            data["user"] = user
            if user["banned_at"]:
                return None
        else:
            data["user"] = None

        return await handler(event, data)
