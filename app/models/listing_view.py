import uuid
from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin, TimestampMixin


class ListingView(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "listing_views"
    __table_args__ = (
        Index("ix_listing_views_listing_id", "listing_id"),
        Index("ix_listing_views_created_at", "created_at"),
    )

    listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("listings.id"))
    viewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
