"""add performance indexes

Revision ID: 007
Revises: 006
Create Date: 2026-06-26
"""
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_listings_section_status_price", "listings", ["section", "status", "price"], if_not_exists=True)
    op.create_index("ix_listings_viloyat_status", "listings", ["viloyat", "status"], if_not_exists=True)
    op.create_index("ix_listings_price", "listings", ["price"], if_not_exists=True)
    op.create_index("ix_listings_is_promoted", "listings", ["is_promoted"], if_not_exists=True)
    op.create_index("ix_messages_unread", "messages", ["conversation_id", "is_read"], if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_messages_unread", "messages")
    op.drop_index("ix_listings_is_promoted", "listings")
    op.drop_index("ix_listings_price", "listings")
    op.drop_index("ix_listings_viloyat_status", "listings")
    op.drop_index("ix_listings_section_status_price", "listings")
