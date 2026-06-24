import uuid
from sqlalchemy import BigInteger, String, Boolean, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_tg_id", "tg_id", unique=True),
        Index("ix_users_ref_code", "ref_code", unique=True),
        Index("ix_users_viloyat", "viloyat"),
    )

    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    viloyat: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    referred_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    ref_code: Mapped[str] = mapped_column(String(20), unique=True)
    ref_count: Mapped[int] = mapped_column(Integer, default=0)
    ref_earnings: Mapped[int] = mapped_column(BigInteger, default=0)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    referrer = relationship("User", remote_side="User.id", foreign_keys=[referred_by])
    shops = relationship("Shop", back_populates="owner")
    listings = relationship("Listing", back_populates="user", foreign_keys="Listing.user_id")
    favourites = relationship("Favourite", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
