from __future__ import annotations

import os
from pathlib import Path

import aiosqlite

_DB_PATH: str = "bot.db"


def set_db_path(path: str) -> None:
    global _DB_PATH
    _DB_PATH = path


async def create_connection() -> aiosqlite.Connection:
    db = await aiosqlite.connect(_DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def ensure_schema(db: aiosqlite.Connection) -> None:
    schema_path = Path(__file__).parent / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    await db.executescript(sql)
    await db.commit()
