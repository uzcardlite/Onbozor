import uuid
from sqlalchemy import String, BigInteger, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import PaymentMethodEnum, PaymentStatusEnum, pg_enum


class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_user_id", "user_id"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_transaction_id", "transaction_id"),
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
    amount: Mapped[int] = mapped_column(BigInteger)
    payment_method: Mapped[PaymentMethodEnum] = mapped_column(
        pg_enum(PaymentMethodEnum, "payment_method_enum")
    )
    transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[PaymentStatusEnum] = mapped_column(
        pg_enum(PaymentStatusEnum, "payment_status_enum"),
        default=PaymentStatusEnum.PENDING,
    )
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)

    user = relationship("User", back_populates="payments")
    shop = relationship("Shop", back_populates="payments")
    listing = relationship("Listing", back_populates="payments")
