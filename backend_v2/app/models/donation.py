from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin


class DonationPaymentSetting(TimestampMixin, Base):
    __tablename__ = "donation_payment_settings_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    method_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(8), index=True)
    currency: Mapped[str | None] = mapped_column(String(16), index=True)
    card_number_masked: Mapped[str | None] = mapped_column(String(64))
    card_number_secret: Mapped[str | None] = mapped_column(Text)
    card_holder_name: Mapped[str | None] = mapped_column(String(255))
    bank_name: Mapped[str | None] = mapped_column(String(255))
    digital_asset_network: Mapped[str | None] = mapped_column(String(64))
    digital_asset_address_secret: Mapped[str | None] = mapped_column(Text)
    digital_asset_address_preview: Mapped[str | None] = mapped_column(String(128))
    instructions: Mapped[str | None] = mapped_column(Text)
    extra_json: Mapped[dict | None] = mapped_column(JSON)
    sort_order: Mapped[int] = mapped_column(BigInteger, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users_v2.id"))
    updated_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users_v2.id"))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
