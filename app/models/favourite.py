import uuid
from sqlalchemy import ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class Favourite(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "favourites"
    __table_args__ = (
        Index("ix_favourites_user_id", "user_id"),
        Index("ix_favourites_user_shop", "user_id", "shop_id", unique=True),
        Index("ix_favourites_user_listing", "user_id", "listing_id", unique=True),
        CheckConstraint(
            "(shop_id IS NOT NULL AND listing_id IS NULL) OR "
            "(shop_id IS NULL AND listing_id IS NOT NULL)",
            name="ck_favourites_one_target",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    shop_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id"), nullable=True
    )
    listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id"), nullable=True
    )

    user = relationship("User", back_populates="favourites")
    shop = relationship("Shop", back_populates="favourites")
    listing = relationship("Listing", back_populates="favourites")
