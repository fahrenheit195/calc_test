from __future__ import annotations

import aiosqlite
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    SuccessfulPayment,
)

from db import queries
from keyboards.inline import buy_credits_keyboard, main_menu_keyboard, subscribe_keyboard
from services.subscriptions import (
    get_daily_credits,
    get_pack_by_id,
    get_sub_by_id,
    tiers_info_text,
)
from utils.formatting import format_balance

router = Router(name="payments")


@router.message(Command("buy"))
async def cmd_buy(message: Message, user: aiosqlite.Row) -> None:
    await message.answer(
        f"🛒 <b>Купить кредиты</b>\n\n"
        f"{format_balance(user)}\n\n"
        "Выберите пакет кредитов:",
        reply_markup=buy_credits_keyboard(),
    )


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message) -> None:
    await message.answer(
        f"💎 <b>Подписки</b>\n\n"
        f"{tiers_info_text()}\n"
        "Выберите подписку:",
        reply_markup=subscribe_keyboard(),
    )


@router.callback_query(lambda c: c.data == "open_buy")
async def cb_open_buy(callback: CallbackQuery, user: aiosqlite.Row) -> None:
    await callback.message.edit_text(  # type: ignore[union-attr]
        f"🛒 <b>Купить кредиты</b>\n\n"
        f"{format_balance(user)}\n\n"
        "Выберите пакет кредитов:",
        reply_markup=buy_credits_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "open_subscribe")
async def cb_open_subscribe(callback: CallbackQuery) -> None:
    await callback.message.edit_text(  # type: ignore[union-attr]
        f"💎 <b>Подписки</b>\n\n"
        f"{tiers_info_text()}\n"
        "Выберите подписку:",
        reply_markup=subscribe_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("buy:"))
async def cb_buy_pack(callback: CallbackQuery) -> None:
    pack_id = (callback.data or "").split(":", 1)[1]
    pack = get_pack_by_id(pack_id)
    if not pack:
        await callback.answer("Пакет не найден.", show_alert=True)
        return

    await callback.bot.send_invoice(  # type: ignore[union-attr]
        chat_id=callback.from_user.id,
        title=f"Кредиты: {pack['credits']} шт.",
        description=f"Пополнение баланса на {pack['credits']} кредитов",
        payload=pack_id,
        currency="XTR",
        prices=[LabeledPrice(label=f"{pack['credits']} кредитов", amount=pack["stars"])],
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("sub:"))
async def cb_buy_sub(callback: CallbackQuery) -> None:
    sub_id = (callback.data or "").split(":", 1)[1]
    sub = get_sub_by_id(sub_id)
    if not sub:
        await callback.answer("Подписка не найдена.", show_alert=True)
        return

    tier_name = sub["tier"].capitalize()
    await callback.bot.send_invoice(  # type: ignore[union-attr]
        chat_id=callback.from_user.id,
        title=f"Подписка {tier_name} — 30 дней",
        description=f"Активация тарифа {tier_name} на 30 дней",
        payload=sub_id,
        currency="XTR",
        prices=[LabeledPrice(label=f"Подписка {tier_name}", amount=sub["stars"])],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(lambda m: m.successful_payment is not None)
async def successful_payment_handler(
    message: Message,
    user: aiosqlite.Row,
    db: aiosqlite.Connection,
) -> None:
    payment: SuccessfulPayment = message.successful_payment  # type: ignore[assignment]
    payload = payment.invoice_payload
    charge_id = payment.telegram_payment_charge_id

    pack = get_pack_by_id(payload)
    if pack:
        await queries.add_credits(
            db, user["user_id"], pack["credits"], "purchase", charge_id
        )
        fresh = await queries.get_user(db, user["user_id"])
        await message.answer(
            f"✅ <b>Оплата прошла успешно!</b>\n\n"
            f"Начислено: <b>{pack['credits']}</b> кредитов\n\n"
            f"{format_balance(fresh)}",
            reply_markup=main_menu_keyboard(),
        )
        return

    sub = get_sub_by_id(payload)
    if sub:
        await queries.set_user_tier(db, user["user_id"], sub["tier"])
        daily = get_daily_credits(sub["tier"])
        await queries.add_credits(
            db, user["user_id"], daily, f"sub_bonus:{sub['tier']}", charge_id
        )
        fresh = await queries.get_user(db, user["user_id"])
        await message.answer(
            f"✅ <b>Подписка активирована!</b>\n\n"
            f"Тариф: <b>{sub['tier'].capitalize()}</b>\n"
            f"Бонус при активации: <b>{daily}</b> кредитов\n\n"
            f"{format_balance(fresh)}",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer("✅ Оплата получена. Спасибо!", reply_markup=main_menu_keyboard())


@router.message(Command("balance"))
async def cmd_balance(
    message: Message, user: aiosqlite.Row, db: aiosqlite.Connection
) -> None:
    fresh = await queries.get_user(db, user["user_id"])
    await message.answer(
        format_balance(fresh),
        reply_markup=main_menu_keyboard(),
    )
