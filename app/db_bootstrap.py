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

_STATEMENTS = [
    # users gamification/verified columns (from migrations 003 / 005)
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS points INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS badges JSONB DEFAULT '[]'",
    # achievements table (from migration 005) — its absence makes award_points
    # raise and (previously) poison the listing-create transaction.
    """CREATE TABLE IF NOT EXISTS achievements (
        id UUID PRIMARY KEY,
        user_id UUID NOT NULL REFERENCES users(id),
        type VARCHAR(50) NOT NULL,
        earned_at TIMESTAMPTZ DEFAULT now(),
        created_at TIMESTAMPTZ DEFAULT now()
    )""",
    "CREATE INDEX IF NOT EXISTS ix_achievements_user_id ON achievements(user_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_achievements_user_type ON achievements(user_id, type)",
]


async def ensure_schema() -> None:
    try:
        async with engine.begin() as conn:
            for stmt in _STATEMENTS:
                await conn.execute(text(stmt))
        logger.info("Schema ensure: user columns + achievements table present")
    except Exception as e:
        logger.error("Schema ensure failed: %s", e, exc_info=True)
