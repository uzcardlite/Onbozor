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
    op.add_column("users", sa.Column("points", sa.Integer, server_default="0"))
    op.add_column("users", sa.Column("level", sa.Integer, server_default="1"))
    op.add_column("users", sa.Column("badges", JSONB, server_default="[]"))

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
