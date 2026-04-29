from __future__ import annotations

from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin


class IntercityRequest(TimestampMixin, Base):
    __tablename__ = "intercity_requests_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mode: Mapped[str] = mapped_column(String(32), default="regular", nullable=False, index=True)
    passenger_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), index=True)
    country_code: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    from_city_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cities_v2.id"))
    to_city_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cities_v2.id"))
    from_text: Mapped[str] = mapped_column(String(255), nullable=False)
    to_text: Mapped[str] = mapped_column(String(255), nullable=False)
    ride_date: Mapped[date | None] = mapped_column(Date)
    ride_time: Mapped[str | None] = mapped_column(String(32))
    seats: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    passenger_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    recommended_price: Mapped[float | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(Text)


class IntercityRoute(TimestampMixin, Base):
    __tablename__ = "intercity_routes_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mode: Mapped[str] = mapped_column(String(32), default="regular", nullable=False, index=True)
    driver_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), index=True)
    country_code: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    from_city_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cities_v2.id"))
    to_city_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cities_v2.id"))
    from_text: Mapped[str] = mapped_column(String(255), nullable=False)
    to_text: Mapped[str] = mapped_column(String(255), nullable=False)
    ride_date: Mapped[date | None] = mapped_column(Date)
    ride_time: Mapped[str | None] = mapped_column(String(32))
    seats_available: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    price_per_seat: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    pickup_mode: Mapped[str] = mapped_column(String(32), default="ask_driver", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(Text)


class IntercityTrip(TimestampMixin, Base):
    __tablename__ = "intercity_trips_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mode: Mapped[str] = mapped_column(String(32), default="regular", nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    passenger_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), index=True)
    driver_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("vehicles_v2.id"))
    final_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="accepted", nullable=False, index=True)
