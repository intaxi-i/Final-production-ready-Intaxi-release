from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixins import TimestampMixin


class DriverProfile(TimestampMixin, Base):
    __tablename__ = "driver_profiles_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="not_started", nullable=False)
    country_code: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    city_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cities_v2.id"))
    license_number: Mapped[str | None] = mapped_column(String(128))
    license_photo_file_id: Mapped[str | None] = mapped_column(String(512))
    identity_photo_file_id: Mapped[str | None] = mapped_column(String(512))
    selfie_file_id: Mapped[str | None] = mapped_column(String(512))
    is_woman_driver_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    woman_driver_status: Mapped[str] = mapped_column(String(32), default="not_requested", nullable=False)
    adult_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users_v2.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    user = relationship("User", foreign_keys=[user_id], back_populates="driver_profile")


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    driver_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), index=True)
    country_code: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    brand: Mapped[str] = mapped_column(String(128), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    year: Mapped[int | None] = mapped_column(BigInteger)
    color: Mapped[str | None] = mapped_column(String(64))
    plate: Mapped[str] = mapped_column(String(64), nullable=False)
    capacity: Mapped[int] = mapped_column(BigInteger, default=4, nullable=False)
    vehicle_class: Mapped[str] = mapped_column(String(32), default="economy", nullable=False)
    photo_front_file_id: Mapped[str | None] = mapped_column(String(512))
    photo_back_file_id: Mapped[str | None] = mapped_column(String(512))
    photo_inside_file_id: Mapped[str | None] = mapped_column(String(512))
    tech_passport_file_id: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    reviewed_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users_v2.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)


class DriverOnlineState(Base):
    __tablename__ = "driver_online_states_v2"

    driver_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), primary_key=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_busy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(8), index=True)
    city_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cities_v2.id"), index=True)
    lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    last_location_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shift_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shift_minutes_today: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DriverPaymentMethod(TimestampMixin, Base):
    __tablename__ = "driver_payment_methods_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    driver_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), index=True)
    country_code: Mapped[str] = mapped_column(String(8), nullable=False)
    method_type: Mapped[str] = mapped_column(String(32), default="card", nullable=False)
    card_number_masked: Mapped[str | None] = mapped_column(String(64))
    card_number_encrypted: Mapped[str | None] = mapped_column(Text)
    card_holder_name: Mapped[str | None] = mapped_column(String(255))
    bank_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
