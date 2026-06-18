from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import (
    CallbackQuery,
    Message,
    PreCheckoutQuery,
    TelegramObject,
)

from keyboards.inline import tos_keyboard

_EXEMPT_COMMANDS = frozenset({"/start", "/help", "/tos"})

TOS_TEXT = (
    "⚠️ <b>Подтверждение возраста и согласие с условиями</b>\n\n"
    "Этот бот генерирует изображения для взрослых (18+).\n\n"
    "Нажимая кнопку ниже, вы подтверждаете:\n"
    "• Вам исполнилось <b>18 лет</b>\n"
    "• Вы даёте согласие на просмотр контента для взрослых\n"
    "• Вы используете бота в личных целях и не нарушаете законы своей страны\n"
    "• Вы не будете публиковать сгенерированный контент несовершеннолетним\n\n"
    "Запрещены промпты с: несовершеннолетними, насилием, незаконным контентом."
)


class ToSGateMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, PreCheckoutQuery):
            return await handler(event, data)

        user = data.get("user")
        if not user:
            return await handler(event, data)

        if user["tos_accepted_at"]:
            return await handler(event, data)

        if isinstance(event, Message):
            text = event.text or ""
            cmd = text.split()[0].lower() if text else ""
            if cmd in _EXEMPT_COMMANDS:
                return await handler(event, data)
            await event.answer(
                TOS_TEXT,
                reply_markup=tos_keyboard(user["user_id"]),
            )
            return None

        if isinstance(event, CallbackQuery):
            cb_data = event.data or ""
            if cb_data.startswith("tos_accept:"):
                return await handler(event, data)
            await event.answer("Сначала примите условия использования.", show_alert=True)
            await event.message.answer(  # type: ignore[union-attr]
                TOS_TEXT,
                reply_markup=tos_keyboard(user["user_id"]),
            )
            return None

        return await handler(event, data)
