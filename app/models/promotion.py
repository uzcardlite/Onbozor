import uuid
from datetime import datetime
from sqlalchemy import String, BigInteger, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import pg_enum

import enum

class PromotionTypeEnum(str, enum.Enum):
    TOP = "top"
    FEATURED = "featured"
    URGENT = "urgent"


class Promotion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "promotions"
    __table_args__ = (
        Index("ix_promotions_listing_id", "listing_id"),
        Index("ix_promotions_user_id", "user_id"),
        Index("ix_promotions_active", "is_active", "expires_at"),
    )

    listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("listings.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    type: Mapped[PromotionTypeEnum] = mapped_column(
        pg_enum(PromotionTypeEnum, "promotion_type_enum")
    )
    price: Mapped[int] = mapped_column(BigInteger)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    listing = relationship("Listing")
    user = relationship("User")
