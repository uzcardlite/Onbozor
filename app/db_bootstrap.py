"""Idempotent schema safety-net run on startup by BOTH the API and the bot.

`alembic upgrade head` cannot repair a DB whose alembic_version already points
at head while the actual columns are missing — it just reports "at head" and
exits. Running these ADD COLUMN IF NOT EXISTS statements directly guarantees the
gamification/verified columns exist regardless of alembic state. Safe to run
from every process that connects to the DB.
"""
import logging

from sqlalchemy import text

from app.database import engine

logger = logging.getLogger("onbozor")

_USER_COLUMNS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS points INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS badges JSONB DEFAULT '[]'",
]


async def ensure_schema() -> None:
    try:
        async with engine.begin() as conn:
            for stmt in _USER_COLUMNS:
                await conn.execute(text(stmt))
        logger.info("Schema ensure: user columns present (is_verified, points, level, badges)")
    except Exception as e:
        logger.error("Schema ensure failed: %s", e, exc_info=True)
