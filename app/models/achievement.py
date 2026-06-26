import uuid
from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin, TimestampMixin


class Achievement(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "achievements"
    __table_args__ = (
        Index("ix_achievements_user_id", "user_id"),
        Index("ix_achievements_user_type", "user_id", "type", unique=True),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(50))
