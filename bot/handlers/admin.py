from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

import aiosqlite
from aiogram import Router
from aiogram.filters import Command, BaseFilter
from aiogram.types import Message

from config import config
from db import queries
from utils.formatting import format_stats

router = Router(name="admin")


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:  # type: ignore[override]
        return message.from_user is not None and message.from_user.id in config.ADMIN_IDS


router.message.filter(AdminFilter())


@router.message(Command("admin_stats"))
async def cmd_admin_stats(message: Message, db: aiosqlite.Connection) -> None:
    now = datetime.utcnow()
    users_count = await queries.get_users_count(db)
    gens_24h = await queries.get_generation_count(db, now - timedelta(hours=24))
    gens_7d = await queries.get_generation_count(db, now - timedelta(days=7))
    await message.answer(format_stats(users_count, gens_24h, gens_7d))


@router.message(Command("admin_grant"))
async def cmd_admin_grant(message: Message, db: aiosqlite.Connection) -> None:
    parts = (message.text or "").split()
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await message.answer("Использование: /admin_grant <user_id> <credits>")
        return

    target_id = int(parts[1])
    amount = int(parts[2])
    user = await queries.get_user(db, target_id)
    if not user:
        await message.answer("Пользователь не найден.")
        return

    await queries.add_credits(db, target_id, amount, "admin_grant")
    await message.answer(f"✅ Начислено {amount} кредитов пользователю {target_id}.")


@router.message(Command("admin_ban"))
async def cmd_admin_ban(message: Message, db: aiosqlite.Connection) -> None:
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /admin_ban <user_id>")
        return

    target_id = int(parts[1])
    await queries.ban_user(db, target_id)
    await message.answer(f"✅ Пользователь {target_id} заблокирован.")


@router.message(Command("admin_unban"))
async def cmd_admin_unban(message: Message, db: aiosqlite.Connection) -> None:
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /admin_unban <user_id>")
        return

    target_id = int(parts[1])
    await queries.unban_user(db, target_id)
    await message.answer(f"✅ Пользователь {target_id} разблокирован.")


@router.message(Command("admin_tier"))
async def cmd_admin_tier(message: Message, db: aiosqlite.Connection) -> None:
    parts = (message.text or "").split()
    if len(parts) != 3 or parts[2] not in ("free", "basic", "premium"):
        await message.answer("Использование: /admin_tier <user_id> <free|basic|premium>")
        return

    target_id = int(parts[1]) if parts[1].isdigit() else 0
    if not target_id:
        await message.answer("Неверный user_id.")
        return

    await queries.set_user_tier(db, target_id, parts[2])
    await message.answer(f"✅ Тариф пользователя {target_id} изменён на {parts[2]}.")


@router.message(Command("admin_broadcast"))
async def cmd_admin_broadcast(message: Message, db: aiosqlite.Connection) -> None:
    text = (message.text or "").split(maxsplit=1)
    if len(text) < 2 or not text[1].strip():
        await message.answer("Использование: /admin_broadcast <текст сообщения>")
        return

    broadcast_text = text[1].strip()
    user_ids = await queries.get_all_user_ids(db)
    sent = 0
    failed = 0

    for uid in user_ids:
        try:
            await message.bot.send_message(uid, broadcast_text)  # type: ignore[union-attr]
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await message.answer(f"📢 Рассылка завершена.\n✅ Отправлено: {sent}\n❌ Ошибок: {failed}")
