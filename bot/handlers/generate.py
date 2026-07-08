from __future__ import annotations

import asyncio
import re

import aiosqlite
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from db import queries
from keyboards.inline import cancel_keyboard, main_menu_keyboard
from services import credits as credit_svc
from services.image_backend import ImageBackend
from services.subscriptions import get_generation_cost
from utils.formatting import format_balance, format_generation_result

router = Router(name="generate")

# English terms match on word boundaries; Russian entries are word stems
# (matched as substrings) so inflected forms are caught without false
# positives like "лет" matching "летом"/"полёт".
_BANNED_RE = re.compile(
    r"\b(child|children|minor|minors|underage|teen|teens|teenager|loli|shota"
    r"|kid|kids|schoolgirl|schoolboy|toddler|infant|preteen)\b"
    r"|несовершеннолет|малолет|школьниц|школьник|ребён|ребен|подрост|младен",
    re.IGNORECASE,
)


def _prompt_safe(prompt: str) -> bool:
    return _BANNED_RE.search(prompt) is None


@router.message(Command(commands=["gen", "generate"]))
async def cmd_generate(
    message: Message,
    user: aiosqlite.Row,
    db: aiosqlite.Connection,
    image_backend: ImageBackend,
) -> None:
    text = message.text or ""
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer(
            "🎨 Укажите промпт после команды.\n"
            "Пример: <code>/gen красивая девушка на закате</code>"
        )
        return

    prompt = parts[1].strip()

    if not _prompt_safe(prompt):
        await message.answer(
            "🚫 Промпт содержит запрещённые слова. "
            "Генерация контента с несовершеннолетними строго запрещена."
        )
        return

    cost = get_generation_cost(user["tier"])
    balance = await credit_svc.get_balance(db, user["user_id"])

    if balance < cost:
        await message.answer(
            f"❌ Недостаточно кредитов.\n"
            f"Нужно: <b>{cost}</b>, у вас: <b>{balance}</b>\n\n"
            "Купите кредиты с помощью /buy",
        )
        return

    status_msg = await message.answer("⏳ Генерирую изображение...")
    backend_name = image_backend.__class__.__name__.replace("Backend", "").lower()

    ok = await credit_svc.check_and_deduct(db, user["user_id"], cost)
    if not ok:
        await status_msg.edit_text(
            "❌ Не удалось списать кредиты. Попробуйте ещё раз."
        )
        return

    try:
        image_bytes = await asyncio.wait_for(
            image_backend.generate(prompt),
            timeout=95,
        )
    except (TimeoutError, asyncio.TimeoutError):
        await credit_svc.refund(db, user["user_id"], cost, "refund:timeout")
        await status_msg.edit_text(
            "⏰ Время ожидания истекло. Кредиты возвращены. Попробуйте позже."
        )
        await queries.log_generation(
            db, user["user_id"], prompt, backend_name, "timeout", None, cost
        )
        return
    except Exception:
        await credit_svc.refund(db, user["user_id"], cost, "refund:backend_error")
        await status_msg.edit_text(
            "❌ Ошибка при генерации. Кредиты возвращены."
        )
        await queries.log_generation(
            db, user["user_id"], prompt, backend_name, "error", None, cost
        )
        return

    fresh = await queries.get_user(db, user["user_id"])
    await status_msg.delete()
    await message.answer_photo(
        photo=BufferedInputFile(image_bytes, filename="image.jpg"),
        caption=f"🎨 <i>{prompt[:200]}</i>\n\n{format_generation_result(fresh['credits'])}",
        reply_markup=main_menu_keyboard(),
    )

    await queries.log_generation(
        db, user["user_id"], prompt, backend_name, "success", None, cost
    )


@router.callback_query(lambda c: c.data == "open_generate")
async def cb_open_generate(callback: CallbackQuery) -> None:
    await callback.message.edit_text(  # type: ignore[union-attr]
        "🎨 <b>Генерация изображений</b>\n\n"
        "Отправьте команду с промптом:\n"
        "<code>/gen ваш промпт на английском</code>\n\n"
        "<b>Советы для лучшего результата:</b>\n"
        "• Пишите промпт на английском языке\n"
        "• Описывайте стиль: <i>photorealistic, anime, oil painting</i>\n"
        "• Добавляйте качество: <i>8k, detailed, masterpiece</i>",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()
