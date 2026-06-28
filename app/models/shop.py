import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, BigInteger, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import SectionEnum, pg_enum


class Shop(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "shops"
    __table_args__ = (
        Index("ix_shops_owner_id", "owner_id"),
        Index("ix_shops_category", "category"),
        Index("ix_shops_viloyat", "viloyat"),
        Index("ix_shops_is_active", "is_active"),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[SectionEnum] = mapped_column(
        pg_enum(SectionEnum, "section_enum")
    )
    viloyat: Mapped[str | None] = mapped_column(String(100), nullable=True)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    monthly_fee: Mapped[int] = mapped_column(BigInteger)
    subscription_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    owner = relationship("User", back_populates="shops")
    listings = relationship("Listing", back_populates="shop")
    favourites = relationship("Favourite", back_populates="shop")
    payments = relationship("Payment", back_populates="shop")
