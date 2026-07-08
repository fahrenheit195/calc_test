from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
import aiosqlite

from db import queries
from keyboards.inline import main_menu_keyboard, tos_keyboard
from middlewares.tos_gate import TOS_TEXT
from utils.formatting import format_balance
from utils.telegram import edit_or_send

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, user: aiosqlite.Row, db: aiosqlite.Connection) -> None:
    if not user["tos_accepted_at"]:
        await message.answer(
            f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
            "Этот бот генерирует изображения для взрослых с помощью ИИ.\n\n"
            "Прежде чем начать, вам нужно принять условия использования:",
            reply_markup=tos_keyboard(user["user_id"]),
        )
        await message.answer(TOS_TEXT)
        return

    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"{format_balance(user)}\n\n"
        "Выберите действие:",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>Команды бота:</b>\n\n"
        "/start — главное меню\n"
        "/gen &lt;промпт&gt; — генерация изображения\n"
        "/balance — баланс кредитов\n"
        "/buy — купить кредиты\n"
        "/subscribe — управление подпиской\n"
        "/tos — условия использования\n\n"
        "<b>Как генерировать:</b>\n"
        "Напишите <code>/gen красивая девушка на пляже</code>"
    )


@router.callback_query(lambda c: c.data == "back_main")
async def cb_back_main(callback: CallbackQuery, user: aiosqlite.Row) -> None:
    await edit_or_send(
        callback,
        f"{format_balance(user)}\n\nВыберите действие:",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "show_balance")
async def cb_show_balance(callback: CallbackQuery, user: aiosqlite.Row, db: aiosqlite.Connection) -> None:
    fresh = await queries.get_user(db, user["user_id"])
    await edit_or_send(
        callback,
        f"{format_balance(fresh)}\n\nВыберите действие:",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()
