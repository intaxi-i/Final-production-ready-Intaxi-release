from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, utcnow


class Wallet(Base):
    __tablename__ = "wallets_v2"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), primary_key=True)
    balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    hold_balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    currency: Mapped[str | None] = mapped_column(String(8))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="wallet")


class WalletLedgerEntry(Base):
    __tablename__ = "wallet_ledger_entries_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), index=True)
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    related_type: Mapped[str | None] = mapped_column(String(64))
    related_id: Mapped[int | None] = mapped_column(BigInteger)
    balance_before: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    balance_after: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users_v2.id"))
    created_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users_v2.id"))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class PaymentTopupRequest(TimestampMixin, Base):
    __tablename__ = "payment_topup_requests_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    driver_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    receipt_file_id: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    reviewed_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users_v2.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
