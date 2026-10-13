import asyncio
import sqlite3
from pathlib import Path

from config import settings


def get_db_path() -> Path:
    return settings.ensure_data_dir() / "users.db"


def init_db() -> None:
    db_file = get_db_path()
    with sqlite3.connect(db_file) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                language_code TEXT NOT NULL
            )
            """
        )
        connection.commit()


def _read_user_language(user_id: int) -> str | None:
    db_file = get_db_path()
    with sqlite3.connect(db_file) as connection:
        cursor = connection.execute(
            "SELECT language_code FROM user_preferences WHERE user_id = ?",
            (user_id,),
        )
        record = cursor.fetchone()
        return record[0] if record else None


def _write_user_language(user_id: int, language_code: str) -> None:
    db_file = get_db_path()
    with sqlite3.connect(db_file) as connection:
        connection.execute(
            """
            INSERT INTO user_preferences (user_id, language_code)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET language_code = excluded.language_code
            """,
            (user_id, language_code),
        )
        connection.commit()


async def get_user_language(user_id: int) -> str | None:
    return await asyncio.to_thread(_read_user_language, user_id)


async def set_user_language(user_id: int, language_code: str) -> None:
    await asyncio.to_thread(_write_user_language, user_id, language_code)
