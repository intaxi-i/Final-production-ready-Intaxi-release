from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin


class CityOrder(TimestampMixin, Base):
    __tablename__ = "city_orders_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mode: Mapped[str] = mapped_column(String(32), default="regular", nullable=False, index=True)
    passenger_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), index=True)
    country_code: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    city_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cities_v2.id"), index=True)
    pickup_address: Mapped[str] = mapped_column(Text, nullable=False)
    pickup_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    pickup_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    destination_address: Mapped[str] = mapped_column(Text, nullable=False)
    destination_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    destination_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    seats: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    passenger_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    recommended_price: Mapped[float | None] = mapped_column(Numeric(14, 2))
    minimum_recommended_price: Mapped[float | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    estimated_distance_km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    estimated_duration_min: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    seen_by_drivers: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    accepted_trip_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CityCounteroffer(TimestampMixin, Base):
    __tablename__ = "city_counteroffers_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("city_orders_v2.id"), index=True)
    driver_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), index=True)
    price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    eta_min: Mapped[int | None] = mapped_column(BigInteger)
    distance_to_pickup_km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CityTrip(TimestampMixin, Base):
    __tablename__ = "city_trips_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mode: Mapped[str] = mapped_column(String(32), default="regular", nullable=False, index=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("city_orders_v2.id"), unique=True, index=True)
    passenger_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), index=True)
    driver_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("vehicles_v2.id"))
    final_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="accepted", nullable=False, index=True)
    pickup_address: Mapped[str] = mapped_column(Text, nullable=False)
    pickup_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    pickup_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    destination_address: Mapped[str] = mapped_column(Text, nullable=False)
    destination_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    destination_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    driver_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    driver_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    passenger_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    passenger_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(Text)
