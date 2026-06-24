"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

section_enum = ENUM("uyjoy", "texnika", "avto", "moto", "kiyim", name="section_enum", create_type=False)
payment_type_enum = ENUM("naqd", "nasiya", "ikkalasi", name="payment_type_enum", create_type=False)
condition_enum = ENUM("yangi", "ishlatilgan", name="condition_enum", create_type=False)
listing_status_enum = ENUM("pending", "active", "rejected", "deleted", name="listing_status_enum", create_type=False)
payment_method_enum = ENUM("payme", "click", name="payment_method_enum", create_type=False)
payment_status_enum = ENUM("pending", "paid", "failed", "cancelled", name="payment_status_enum", create_type=False)
notification_type_enum = ENUM(
    "new_listing", "listing_approved", "listing_rejected",
    "shop_approved", "payment_success", "referral", "system",
    name="notification_type_enum", create_type=False,
)


def upgrade() -> None:
    # ── ENUMs ──
    op.execute("CREATE TYPE section_enum AS ENUM ('uyjoy','texnika','avto','moto','kiyim')")
    op.execute("CREATE TYPE payment_type_enum AS ENUM ('naqd','nasiya','ikkalasi')")
    op.execute("CREATE TYPE condition_enum AS ENUM ('yangi','ishlatilgan')")
    op.execute("CREATE TYPE listing_status_enum AS ENUM ('pending','active','rejected','deleted')")
    op.execute("CREATE TYPE payment_method_enum AS ENUM ('payme','click')")
    op.execute("CREATE TYPE payment_status_enum AS ENUM ('pending','paid','failed','cancelled')")
    op.execute(
        "CREATE TYPE notification_type_enum AS ENUM ("
        "'new_listing','listing_approved','listing_rejected',"
        "'shop_approved','payment_success','referral','system')"
    )

    # ── users ──
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tg_id", sa.BigInteger, nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("viloyat", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("referred_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("ref_code", sa.String(20), nullable=False),
        sa.Column("ref_count", sa.Integer, server_default="0"),
        sa.Column("ref_earnings", sa.BigInteger, server_default="0"),
        sa.Column("is_blocked", sa.Boolean, server_default="false"),
        sa.Column("is_admin", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_tg_id", "users", ["tg_id"], unique=True)
    op.create_index("ix_users_ref_code", "users", ["ref_code"], unique=True)
    op.create_index("ix_users_viloyat", "users", ["viloyat"])

    # ── shops ──
    op.create_table(
        "shops",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category", section_enum, nullable=False),
        sa.Column("viloyat", sa.String(100), nullable=True),
        sa.Column("icon_url", sa.String(500), nullable=True),
        sa.Column("is_verified", sa.Boolean, server_default="false"),
        sa.Column("is_active", sa.Boolean, server_default="false"),
        sa.Column("monthly_fee", sa.BigInteger, nullable=False),
        sa.Column("subscription_expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_shops_owner_id", "shops", ["owner_id"])
    op.create_index("ix_shops_category", "shops", ["category"])
    op.create_index("ix_shops_viloyat", "shops", ["viloyat"])
    op.create_index("ix_shops_is_active", "shops", ["is_active"])

    # ── listings ──
    op.create_table(
        "listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("shop_id", UUID(as_uuid=True), sa.ForeignKey("shops.id"), nullable=True),
        sa.Column("section", section_enum, nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("subcategory", sa.String(100), nullable=True),
        sa.Column("payment_type", payment_type_enum, nullable=False),
        sa.Column("condition", condition_enum, nullable=False),
        sa.Column("price", sa.BigInteger, nullable=False),
        sa.Column("negotiable", sa.Boolean, server_default="false"),
        sa.Column("viloyat", sa.String(100), nullable=False),
        sa.Column("seller_username", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("image_urls", JSONB, server_default="[]"),
        sa.Column("views", sa.Integer, server_default="0"),
        sa.Column("is_promoted", sa.Boolean, server_default="false"),
        sa.Column("promoted_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", listing_status_enum, server_default="pending"),
        sa.Column("reject_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_listings_user_id", "listings", ["user_id"])
    op.create_index("ix_listings_shop_id", "listings", ["shop_id"])
    op.create_index("ix_listings_section", "listings", ["section"])
    op.create_index("ix_listings_status", "listings", ["status"])
    op.create_index("ix_listings_viloyat", "listings", ["viloyat"])
    op.create_index("ix_listings_section_viloyat_status", "listings", ["section", "viloyat", "status"])
    op.create_index("ix_listings_created_at", "listings", ["created_at"])

    # ── favourites ──
    op.create_table(
        "favourites",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("shop_id", UUID(as_uuid=True), sa.ForeignKey("shops.id"), nullable=True),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("listings.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "(shop_id IS NOT NULL AND listing_id IS NULL) OR "
            "(shop_id IS NULL AND listing_id IS NOT NULL)",
            name="ck_favourites_one_target",
        ),
    )
    op.create_index("ix_favourites_user_id", "favourites", ["user_id"])
    op.create_index("ix_favourites_user_shop", "favourites", ["user_id", "shop_id"], unique=True)
    op.create_index("ix_favourites_user_listing", "favourites", ["user_id", "listing_id"], unique=True)

    # ── payments ──
    op.create_table(
        "payments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("shop_id", UUID(as_uuid=True), sa.ForeignKey("shops.id"), nullable=True),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("listings.id"), nullable=True),
        sa.Column("amount", sa.BigInteger, nullable=False),
        sa.Column("payment_method", payment_method_enum, nullable=False),
        sa.Column("transaction_id", sa.String(255), nullable=True),
        sa.Column("status", payment_status_enum, server_default="pending"),
        sa.Column("payload", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_payments_transaction_id", "payments", ["transaction_id"])

    # ── broadcasts ──
    op.create_table(
        "broadcasts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("admin_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("message_text", sa.Text, nullable=False),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("sent_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── notifications ──
    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", notification_type_enum, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("is_read", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_user_unread", "notifications", ["user_id", "is_read"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("broadcasts")
    op.drop_table("payments")
    op.drop_table("favourites")
    op.drop_table("listings")
    op.drop_table("shops")
    op.drop_table("users")
    op.execute("DROP TYPE notification_type_enum")
    op.execute("DROP TYPE payment_status_enum")
    op.execute("DROP TYPE payment_method_enum")
    op.execute("DROP TYPE listing_status_enum")
    op.execute("DROP TYPE condition_enum")
    op.execute("DROP TYPE payment_type_enum")
    op.execute("DROP TYPE section_enum")
