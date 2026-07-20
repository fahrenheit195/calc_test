from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
import aiosqlite

from db import queries
from keyboards.inline import main_menu_keyboard, tos_keyboard
from middlewares.tos_gate import TOS_TEXT
from services.subscriptions import get_daily_credits
from utils.formatting import format_balance

router = Router(name="tos")


@router.message(Command("tos"))
async def cmd_tos(message: Message, user: aiosqlite.Row) -> None:
    if user["tos_accepted_at"]:
        await message.answer(
            "✅ Вы уже приняли условия использования.\n\n" + TOS_TEXT
        )
    else:
        await message.answer(TOS_TEXT, reply_markup=tos_keyboard(user["user_id"]))


@router.callback_query(lambda c: c.data and c.data.startswith("tos_accept:"))
async def cb_tos_accept(
    callback: CallbackQuery, user: aiosqlite.Row, db: aiosqlite.Connection
) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer("Неверные данные.", show_alert=True)
        return

    target_id = int(parts[1])
    if target_id != callback.from_user.id:
        await callback.answer("Эта кнопка не для вас.", show_alert=True)
        return

    if user["tos_accepted_at"]:
        await callback.answer("Вы уже приняли условия.", show_alert=False)
        return

    await queries.set_tos_accepted(db, user["user_id"])
    # Grant the welcome credits through the daily-refresh path so
    # last_daily_refresh is stamped and the same day isn't credited twice.
    daily = get_daily_credits(user["tier"])
    await queries.refresh_daily_credits(db, user["user_id"], daily)

    fresh = await queries.get_user(db, user["user_id"])
    await callback.message.edit_text(  # type: ignore[union-attr]
        f"✅ <b>Условия приняты!</b>\n\n"
        f"Вы получили <b>{daily}</b> стартовых кредитов.\n\n"
        f"{format_balance(fresh)}\n\n"
        "Выберите действие:",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer("Добро пожаловать!")
