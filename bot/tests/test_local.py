"""Offline integration test — no network, no Telegram token, no image API.

Spins up the real Dispatcher (all middlewares + routers) and feeds it fake
Updates through a recording Bot session, asserting both the bot's outgoing
API calls and the resulting DB state.

Run:  cd bot && python -m tests.test_local
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone
from itertools import count

# Env must be set before importing config-dependent modules.
os.environ.setdefault("BOT_TOKEN", "123456789:TEST_TOKEN_FOR_LOCAL_ONLY")
os.environ.setdefault("ADMIN_IDS", "999")
os.environ.setdefault("RATE_LIMIT_MAX", "1000")  # keep the limiter out of the way

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.enums import ParseMode
from aiogram.types import (
    CallbackQuery,
    Chat,
    Message,
    SuccessfulPayment,
    Update,
    User,
)

from config import config
from db import queries
from db.connection import create_connection, ensure_schema, set_db_path
from handlers import admin, generate, payments, start, tos
from middlewares.rate_limit import RateLimitMiddleware
from middlewares.tos_gate import ToSGateMiddleware
from middlewares.user_loader import UserLoaderMiddleware
from services.image_backend import ImageBackend

_ids = count(1000)
_updates = count(1)


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #
class RecordingSession(BaseSession):
    """Intercepts every outgoing Telegram API call instead of hitting network."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list = []

    async def make_request(self, bot, method, timeout=None):  # type: ignore[override]
        self.calls.append(method)
        ret = str(getattr(method, "__returning__", bool))
        if "Message" in ret:
            # Bind to the bot like the real API does, so chained calls
            # (e.g. status_msg.delete()) have a bot instance.
            return _fake_bot_message().as_(bot)
        return True

    async def stream_content(self, *a, **k):  # type: ignore[override]
        yield b""

    async def close(self) -> None:
        pass


class FakeImageBackend(ImageBackend):
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def generate(self, prompt: str, negative_prompt: str = "") -> bytes:
        self.calls.append(prompt)
        return b"\xff\xd8\xff\xe0FAKEJPEG"  # dummy bytes, no network


def _fake_bot_message() -> Message:
    return Message(
        message_id=next(_ids),
        date=datetime.now(timezone.utc),
        chat=Chat(id=1, type="private"),
        from_user=User(id=0, is_bot=True, first_name="bot"),
        text="ok",
    )


def _user(uid: int) -> User:
    return User(id=uid, is_bot=False, first_name=f"User{uid}", username=f"u{uid}")


def _text_update(uid: int, text: str, payment: SuccessfulPayment | None = None) -> Update:
    return Update(
        update_id=next(_updates),
        message=Message(
            message_id=next(_ids),
            date=datetime.now(timezone.utc),
            chat=Chat(id=uid, type="private"),
            from_user=_user(uid),
            text=text if payment is None else None,
            successful_payment=payment,
        ),
    )


def _callback_update(uid: int, data: str) -> Update:
    return Update(
        update_id=next(_updates),
        callback_query=CallbackQuery(
            id=str(next(_ids)),
            from_user=_user(uid),
            chat_instance="ci",
            data=data,
            message=Message(
                message_id=next(_ids),
                date=datetime.now(timezone.utc),
                chat=Chat(id=uid, type="private"),
                from_user=User(id=0, is_bot=True, first_name="bot"),
                text="menu",
            ),
        ),
    )


def _payment(payload: str, amount: int) -> SuccessfulPayment:
    return SuccessfulPayment(
        currency="XTR",
        total_amount=amount,
        invoice_payload=payload,
        telegram_payment_charge_id=f"charge_{payload}",
        provider_payment_charge_id="prov",
    )


# --------------------------------------------------------------------------- #
# Assertion helpers
# --------------------------------------------------------------------------- #
PASSED = 0


def check(name: str, cond: bool) -> None:
    global PASSED
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {name}")
    if not cond:
        raise AssertionError(name)
    PASSED += 1


def last_texts(session: RecordingSession) -> str:
    parts = []
    for m in session.calls:
        for attr in ("text", "caption"):
            v = getattr(m, attr, None)
            if v:
                parts.append(v)
    return "\n".join(parts)


def method_names(session: RecordingSession) -> list[str]:
    return [type(m).__name__ for m in session.calls]


# --------------------------------------------------------------------------- #
# Test scenario
# --------------------------------------------------------------------------- #
async def run() -> None:
    set_db_path(":memory:")
    db = await create_connection()
    await ensure_schema(db)

    backend = FakeImageBackend()
    session = RecordingSession()
    bot = Bot(
        token=config.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp["db"] = db
    dp["image_backend"] = backend
    dp.update.middleware(UserLoaderMiddleware())
    dp.message.middleware(RateLimitMiddleware())
    dp.message.middleware(ToSGateMiddleware())
    dp.callback_query.middleware(ToSGateMiddleware())
    for r in (tos.router, start.router, generate.router, payments.router, admin.router):
        dp.include_router(r)

    UID = 123
    ADMIN = 999

    async def feed(update: Update) -> RecordingSession:
        session.calls.clear()
        backend.calls.clear()
        await dp.feed_update(bot, update)
        return session

    print("\n1. /start for a new user → ToS gate shown, user row created")
    await feed(_text_update(UID, "/start"))
    u = await queries.get_user(db, UID)
    check("user created with 0 credits", u is not None and u["credits"] == 0)
    check("ToS text offered", "18" in last_texts(session))

    print("\n2. Any command before ToS is blocked by the gate")
    s = await feed(_text_update(UID, "/gen a cat"))
    check("generation blocked pre-ToS", backend.calls == [])
    check("gate re-prompts ToS", "18" in last_texts(s))

    print("\n3. Accept ToS via callback → welcome credits granted once")
    await feed(_callback_update(UID, f"tos_accept:{UID}"))
    u = await queries.get_user(db, UID)
    check("tos_accepted_at set", u["tos_accepted_at"] is not None)
    check("welcome credits = 3 (free tier)", u["credits"] == 3)

    print("\n4. Foreign ToS button (wrong user id) is rejected")
    await feed(_callback_update(UID, "tos_accept:88888"))
    u = await queries.get_user(db, UID)
    check("credits unchanged after foreign button", u["credits"] == 3)

    print("\n5. /gen without a prompt → usage hint, no charge")
    s = await feed(_text_update(UID, "/gen"))
    check("no backend call", backend.calls == [])
    u = await queries.get_user(db, UID)
    check("no credits deducted", u["credits"] == 3)

    print("\n6. /gen with a prompt → image generated, 3 credits charged")
    s = await feed(_text_update(UID, "/gen sunset over the ocean"))
    check("backend invoked once", backend.calls == ["sunset over the ocean"])
    check("photo sent", "SendPhoto" in method_names(s))
    u = await queries.get_user(db, UID)
    check("balance 3 → 0", u["credits"] == 0)

    print("\n7. /gen with empty balance → insufficient-credits message")
    s = await feed(_text_update(UID, "/gen another one"))
    check("backend NOT called", backend.calls == [])
    check("insufficient message", "Недостаточно" in last_texts(s))

    print("\n8. Banned prompt → refused before any charge")
    await queries.add_credits(db, UID, 10, "test_topup")
    s = await feed(_text_update(UID, "/gen young teen girl"))
    check("banned backend NOT called", backend.calls == [])
    check("refusal shown", "запрещ" in last_texts(s).lower())
    u = await queries.get_user(db, UID)
    check("no charge for banned prompt", u["credits"] == 10)

    print("\n9. /buy → invoice offer, then buy callback sends XTR invoice")
    await feed(_text_update(UID, "/buy"))
    s = await feed(_callback_update(UID, "buy:pack_50"))
    invoices = [m for m in session.calls if type(m).__name__ == "SendInvoice"]
    check("SendInvoice emitted", len(invoices) == 1)
    check("currency is XTR (Stars)", invoices and invoices[0].currency == "XTR")

    print("\n10. SuccessfulPayment(pack_50) → +50 credits (gate/limiter exempt)")
    before = (await queries.get_user(db, UID))["credits"]
    await feed(_text_update(UID, "", payment=_payment("pack_50", 50)))
    u = await queries.get_user(db, UID)
    check("credits += 50", u["credits"] == before + 50)

    print("\n11. SuccessfulPayment(sub_premium) → tier upgraded with expiry")
    await feed(_text_update(UID, "", payment=_payment("sub_premium", 400)))
    u = await queries.get_user(db, UID)
    check("tier is premium", u["tier"] == "premium")
    check("expiry stamped", u["tier_expires_at"] is not None)

    print("\n12. Admin /admin_stats works for admin, ignored for normal user")
    s = await feed(_text_update(ADMIN, "/admin_stats"))
    check("admin gets stats", "Статистика" in last_texts(s))
    s = await feed(_text_update(UID, "/admin_stats"))
    check("non-admin gets nothing", "Статистика" not in last_texts(s))

    print("\n13. Banned user is dropped by UserLoader middleware")
    await queries.ban_user(db, UID)
    s = await feed(_text_update(UID, "/balance"))
    check("banned user gets no response", session.calls == [])

    await bot.session.close()
    await db.close()
    print(f"\n✅ ALL {PASSED} CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(run())
