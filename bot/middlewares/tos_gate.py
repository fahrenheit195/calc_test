from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from keyboards.inline import tos_keyboard

_EXEMPT_COMMANDS = frozenset({"/start", "/help", "/tos"})

TOS_TEXT = (
    "⚠️ <b>Подтверждение возраста и согласие с условиями</b>\n\n"
    "Этот бот генерирует изображения для взрослых (18+).\n\n"
    "Нажимая кнопку ниже, вы подтверждаете:\n"
    "• Вам исполнилось <b>18 лет</b>\n"
    "• Вы даёте согласие на просмотр контента для взрослых\n"
    "• Вы используете бота в личных целях и не нарушаете законы своей страны\n"
    "• Вы не будете показывать сгенерированный контент несовершеннолетним\n\n"
    "Запрещены промпты с: несовершеннолетними, насилием, незаконным контентом."
)


class ToSGateMiddleware(BaseMiddleware):
    """Registered on dp.message and dp.callback_query, so `event` is the
    concrete Message / CallbackQuery, not the raw Update."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("user")
        if not user or user["tos_accepted_at"]:
            return await handler(event, data)

        if isinstance(event, Message):
            # Never block payment confirmations: Telegram already charged
            # the user, credits must be granted.
            if event.successful_payment:
                return await handler(event, data)
            text = event.text or ""
            cmd = text.split()[0].split("@")[0].lower() if text else ""
            if cmd in _EXEMPT_COMMANDS:
                return await handler(event, data)
            await event.answer(
                TOS_TEXT,
                reply_markup=tos_keyboard(user["user_id"]),
            )
            return None

        if isinstance(event, CallbackQuery):
            if (event.data or "").startswith("tos_accept:"):
                return await handler(event, data)
            await event.answer(
                "Сначала подтвердите возраст (18+) — отправьте /start.",
                show_alert=True,
            )
            return None

        return await handler(event, data)
