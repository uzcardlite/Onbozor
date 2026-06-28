"""add gamification: points, level, badges, achievements

Revision ID: 005
Revises: 004
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotent so re-running the chain on a partially-migrated DB never fails.
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS points INTEGER DEFAULT 0")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS badges JSONB DEFAULT '[]'")

    op.create_table(
        "achievements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("earned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_achievements_user_id", "achievements", ["user_id"])
    op.create_index("ix_achievements_user_type", "achievements", ["user_id", "type"], unique=True)


def downgrade() -> None:
    op.drop_table("achievements")
    op.drop_column("users", "badges")
    op.drop_column("users", "level")
    op.drop_column("users", "points")
