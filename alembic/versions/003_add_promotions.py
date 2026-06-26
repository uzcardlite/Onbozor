"""add promotions and user verified

Revision ID: 003
Revises: 002
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE promotion_type_enum AS ENUM ('top','featured','urgent')")

    op.create_table(
        "promotions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("listings.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", ENUM("top", "featured", "urgent", name="promotion_type_enum", create_type=False), nullable=False),
        sa.Column("price", sa.BigInteger, nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_promotions_listing_id", "promotions", ["listing_id"])
    op.create_index("ix_promotions_user_id", "promotions", ["user_id"])
    op.create_index("ix_promotions_active", "promotions", ["is_active", "expires_at"])

    op.add_column("users", sa.Column("is_verified", sa.Boolean, server_default="false"))


def downgrade() -> None:
    op.drop_column("users", "is_verified")
    op.drop_table("promotions")
    op.execute("DROP TYPE promotion_type_enum")
