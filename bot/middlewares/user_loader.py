from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

import aiosqlite
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from db import queries
from services.subscriptions import get_daily_credits


class UserLoaderMiddleware(BaseMiddleware):
    """Registered on dp.update. Relies on aiogram's built-in
    UserContextMiddleware (an outer middleware) having put
    `event_from_user` into `data` already."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from_user = data.get("event_from_user")
        if not from_user or from_user.is_bot:
            data["user"] = None
            return await handler(event, data)

        db: aiosqlite.Connection = data["db"]
        user = await queries.get_or_create_user(db, from_user.id, from_user.username)

        if user["banned_at"]:
            return None

        # Downgrade expired paid subscriptions
        if user["tier"] != "free" and user["tier_expires_at"]:
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            if user["tier_expires_at"] <= now_str:
                await queries.set_user_tier(db, user["user_id"], "free", None)
                user = await queries.get_user(db, user["user_id"])

        # Daily free credits, once per day, only after ToS acceptance
        if user["tos_accepted_at"]:
            refreshed = await queries.refresh_daily_credits(
                db, user["user_id"], get_daily_credits(user["tier"])
            )
            if refreshed:
                user = await queries.get_user(db, user["user_id"])

        data["user"] = user
        return await handler(event, data)
