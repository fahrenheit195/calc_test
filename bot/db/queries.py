from __future__ import annotations

import time
from datetime import datetime, date
from typing import Optional

import aiosqlite


async def get_or_create_user(
    db: aiosqlite.Connection, user_id: int, username: Optional[str]
) -> aiosqlite.Row:
    await db.execute(
        """
        INSERT INTO users (user_id, username, credits)
        VALUES (?, ?, 0)
        ON CONFLICT(user_id) DO UPDATE SET username = excluded.username
        """,
        (user_id, username),
    )
    await db.commit()
    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return await cursor.fetchone()


async def get_user(db: aiosqlite.Connection, user_id: int) -> Optional[aiosqlite.Row]:
    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return await cursor.fetchone()


async def set_tos_accepted(db: aiosqlite.Connection, user_id: int) -> None:
    await db.execute(
        "UPDATE users SET tos_accepted_at = CURRENT_TIMESTAMP WHERE user_id = ?",
        (user_id,),
    )
    await db.commit()


async def deduct_credits(db: aiosqlite.Connection, user_id: int, amount: int) -> bool:
    cursor = await db.execute(
        "UPDATE users SET credits = credits - ? WHERE user_id = ? AND credits >= ?",
        (amount, user_id, amount),
    )
    await db.commit()
    return cursor.rowcount == 1


async def add_credits(
    db: aiosqlite.Connection,
    user_id: int,
    amount: int,
    reason: str,
    charge_id: Optional[str] = None,
) -> None:
    await db.execute(
        "UPDATE users SET credits = credits + ? WHERE user_id = ?",
        (amount, user_id),
    )
    await db.execute(
        "INSERT INTO transactions (user_id, delta, reason, telegram_payment_charge_id) VALUES (?, ?, ?, ?)",
        (user_id, amount, reason, charge_id),
    )
    await db.commit()


async def log_generation(
    db: aiosqlite.Connection,
    user_id: int,
    prompt: str,
    backend: str,
    status: str,
    image_url: Optional[str],
    credits_cost: int,
) -> None:
    await db.execute(
        """
        INSERT INTO generations (user_id, prompt, backend, status, image_url, credits_cost)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, prompt, backend, status, image_url, credits_cost),
    )
    await db.commit()


async def set_user_tier(
    db: aiosqlite.Connection,
    user_id: int,
    tier: str,
    expires_at: Optional[str] = None,
) -> None:
    await db.execute(
        "UPDATE users SET tier = ?, tier_expires_at = ? WHERE user_id = ?",
        (tier, expires_at, user_id),
    )
    await db.commit()


async def ban_user(db: aiosqlite.Connection, user_id: int) -> None:
    await db.execute(
        "UPDATE users SET banned_at = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,)
    )
    await db.commit()


async def unban_user(db: aiosqlite.Connection, user_id: int) -> None:
    await db.execute("UPDATE users SET banned_at = NULL WHERE user_id = ?", (user_id,))
    await db.commit()


async def check_and_increment_rate_limit(
    db: aiosqlite.Connection, user_id: int, window: int, max_count: int
) -> bool:
    window_start = int(time.time()) // window * window
    cursor = await db.execute(
        """
        INSERT INTO rate_limit_log (user_id, window_start, count) VALUES (?, ?, 1)
        ON CONFLICT(user_id, window_start) DO UPDATE SET count = count + 1
        RETURNING count
        """,
        (user_id, window_start),
    )
    row = await cursor.fetchone()
    await db.execute(
        "DELETE FROM rate_limit_log WHERE window_start < ?",
        (window_start - window,),
    )
    await db.commit()
    return row["count"] <= max_count


async def get_all_user_ids(db: aiosqlite.Connection) -> list[int]:
    cursor = await db.execute(
        "SELECT user_id FROM users WHERE banned_at IS NULL"
    )
    rows = await cursor.fetchall()
    return [r["user_id"] for r in rows]


async def get_users_count(db: aiosqlite.Connection) -> int:
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
    row = await cursor.fetchone()
    return row["cnt"]


async def get_generation_count(
    db: aiosqlite.Connection, since: datetime
) -> int:
    # SQLite CURRENT_TIMESTAMP stores "YYYY-MM-DD HH:MM:SS" (no "T"),
    # so the comparison string must use the same format.
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM generations WHERE created_at >= ?",
        (since.strftime("%Y-%m-%d %H:%M:%S"),),
    )
    row = await cursor.fetchone()
    return row["cnt"]


async def refresh_daily_credits(
    db: aiosqlite.Connection, user_id: int, amount: int
) -> bool:
    today = date.today().isoformat()
    cursor = await db.execute(
        "SELECT last_daily_refresh FROM users WHERE user_id = ?", (user_id,)
    )
    row = await cursor.fetchone()
    if row and row["last_daily_refresh"] == today:
        return False
    await db.execute(
        "UPDATE users SET credits = credits + ?, last_daily_refresh = ? WHERE user_id = ?",
        (amount, today, user_id),
    )
    await db.execute(
        "INSERT INTO transactions (user_id, delta, reason) VALUES (?, ?, ?)",
        (user_id, amount, "daily_refresh"),
    )
    await db.commit()
    return True
