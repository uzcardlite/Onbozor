import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, BigInteger, Integer, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import SectionEnum, PaymentTypeEnum, ConditionEnum, ListingStatusEnum


class Listing(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "listings"
    __table_args__ = (
        Index("ix_listings_user_id", "user_id"),
        Index("ix_listings_shop_id", "shop_id"),
        Index("ix_listings_section", "section"),
        Index("ix_listings_status", "status"),
        Index("ix_listings_viloyat", "viloyat"),
        Index("ix_listings_section_viloyat_status", "section", "viloyat", "status"),
        Index("ix_listings_created_at", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    shop_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id"), nullable=True
    )
    section: Mapped[SectionEnum] = mapped_column(
        ENUM(SectionEnum, name="section_enum", create_type=False)
    )
    category: Mapped[str] = mapped_column(String(100))
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payment_type: Mapped[PaymentTypeEnum] = mapped_column(
        ENUM(PaymentTypeEnum, name="payment_type_enum", create_type=False)
    )
    condition: Mapped[ConditionEnum] = mapped_column(
        ENUM(ConditionEnum, name="condition_enum", create_type=False)
    )
    price: Mapped[int] = mapped_column(BigInteger)
    negotiable: Mapped[bool] = mapped_column(Boolean, default=False)
    viloyat: Mapped[str] = mapped_column(String(100))
    seller_username: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    image_urls: Mapped[list] = mapped_column(JSONB, default=list)
    views: Mapped[int] = mapped_column(Integer, default=0)
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    promoted_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[ListingStatusEnum] = mapped_column(
        ENUM(ListingStatusEnum, name="listing_status_enum", create_type=False),
        default=ListingStatusEnum.PENDING,
    )
    reject_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="listings", foreign_keys=[user_id])
    shop = relationship("Shop", back_populates="listings")
    favourites = relationship("Favourite", back_populates="listing")
    payments = relationship("Payment", back_populates="listing")
