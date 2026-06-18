from __future__ import annotations

import aiosqlite

from db import queries


async def check_and_deduct(db: aiosqlite.Connection, user_id: int, amount: int) -> bool:
    return await queries.deduct_credits(db, user_id, amount)


async def get_balance(db: aiosqlite.Connection, user_id: int) -> int:
    user = await queries.get_user(db, user_id)
    return user["credits"] if user else 0


async def refund(
    db: aiosqlite.Connection, user_id: int, amount: int, reason: str
) -> None:
    await queries.add_credits(db, user_id, amount, reason)
