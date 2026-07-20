from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.subscriptions import CREDIT_PACKS, SUBSCRIPTION_PACKS


def tos_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Я подтверждаю — мне 18+ лет",
        callback_data=f"tos_accept:{user_id}",
    )
    return builder.as_markup()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎨 Сгенерировать", callback_data="open_generate")
    builder.button(text="💰 Баланс", callback_data="show_balance")
    builder.button(text="🛒 Купить кредиты", callback_data="open_buy")
    builder.button(text="💎 Подписки", callback_data="open_subscribe")
    builder.adjust(2)
    return builder.as_markup()


def buy_credits_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pack in CREDIT_PACKS:
        builder.button(text=pack["label"], callback_data=f"buy:{pack['id']}")
    builder.button(text="◀️ Назад", callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()


def subscribe_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sub in SUBSCRIPTION_PACKS:
        builder.button(text=sub["label"], callback_data=f"sub:{sub['id']}")
    builder.button(text="◀️ Назад", callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="back_main")
    return builder.as_markup()
