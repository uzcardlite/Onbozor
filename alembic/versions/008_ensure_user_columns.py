"""ensure user gamification/verified columns exist (idempotent safety net)

These columns are originally added by 003 (is_verified) and 005
(points, level, badges). This migration re-asserts them with
ADD COLUMN IF NOT EXISTS so a DB that is missing them — e.g. one that was
never upgraded past revision 002 — is brought fully up to date even if the
intermediate revisions did not run.

Revision ID: 008
Revises: 007
Create Date: 2026-06-28
"""
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS points INTEGER DEFAULT 0")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS badges JSONB DEFAULT '[]'")


def downgrade() -> None:
    # No-op: these columns are owned by migrations 003 / 005.
    pass
