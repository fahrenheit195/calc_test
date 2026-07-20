from __future__ import annotations

from typing import Optional

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message


async def edit_or_send(
    callback: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> None:
    """Edit the callback's message when possible, otherwise send a new one.

    Media messages (e.g. generated photos with a menu keyboard) have no text
    to edit, and callback.message can be an InaccessibleMessage — in both
    cases edit_text would raise.
    """
    msg = callback.message
    if isinstance(msg, Message) and msg.text:
        await msg.edit_text(text, reply_markup=reply_markup)
    elif isinstance(msg, Message):
        await msg.answer(text, reply_markup=reply_markup)
    else:
        await callback.bot.send_message(
            callback.from_user.id, text, reply_markup=reply_markup
        )
