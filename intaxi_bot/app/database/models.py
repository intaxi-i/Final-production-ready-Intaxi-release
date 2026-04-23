from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, inspect, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / 'db.sqlite3'
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite+aiosqlite:///{DB_PATH}')

engine = create_async_engine(DATABASE_URL, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default='')
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default='ru')
    country: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    commission_due: Mapped[float] = mapped_column(Float, default=0.0)
    total_commission_paid: Mapped[float] = mapped_column(Float, default=0.0)
    free_rides_left: Mapped[int] = mapped_column(Integer, default=0)
    active_role: Mapped[str] = mapped_column(String(32), default='passenger')
    driver_card_country: Mapped[str | None] = mapped_column(String(32), nullable=True)
    driver_card_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    vehicle: Mapped['Vehicle | None'] = relationship(back_populates='user', uselist=False)


class Vehicle(Base):
    __tablename__ = 'vehicles'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True)
    brand: Mapped[str] = mapped_column(String(128))
    model: Mapped[str] = mapped_column(String(128))
    plate: Mapped[str] = mapped_column(String(64))
    color: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capacity: Mapped[str | None] = mapped_column(String(16), nullable=True)
    vehicle_class: Mapped[str] = mapped_column(String(16), default='class4')
    accepts_class4: Mapped[bool] = mapped_column(Boolean, default=True)
    accepts_class7: Mapped[bool] = mapped_column(Boolean, default=False)
    photo_tech: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_license: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_out: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_in: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_tech_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_license_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_out_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_in_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates='vehicle')


class AdminRole(Base):
    __tablename__ = 'admin_roles'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(Integer, index=True)
    role: Mapped[str] = mapped_column(String(32), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint('tg_id', 'role', name='uq_admin_role_active'),)


class DriverPaymentRequest(Base):
    __tablename__ = 'driver_payment_requests'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_tg_id: Mapped[int] = mapped_column(Integer, index=True)
    card_country: Mapped[str | None] = mapped_column(String(32), nullable=True)
    admin_card_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    receipt_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default='pending')
    reviewed_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FeedbackEntry(Base):
    __tablename__ = 'feedback_entries'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_tg_id: Mapped[int] = mapped_column(Integer, index=True)
    kind: Mapped[str] = mapped_column(String(32), default='feedback')
    content_type: Mapped[str] = mapped_column(String(16), default='text')
    text_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MessageCleanup(Base):
    __tablename__ = 'message_cleanup'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_tg_id: Mapped[int] = mapped_column(Integer, index=True)
    chat_id: Mapped[int] = mapped_column(Integer)
    message_id: Mapped[int] = mapped_column(Integer)
    context: Mapped[str] = mapped_column(String(64), default='admin')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint('user_tg_id', 'message_id', name='uq_cleanup_message'),)


class CityOrderV1(Base):
    __tablename__ = 'city_orders_v1'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    creator_tg_id: Mapped[int] = mapped_column(Integer, index=True)
    role: Mapped[str] = mapped_column(String(32))
    country: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city: Mapped[str] = mapped_column(String(255))
    from_address: Mapped[str] = mapped_column(String(255))
    to_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seats: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    accepted_by_tg_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default='active')
    created_at: Mapped[str] = mapped_column(String(64), default=lambda: utcnow().replace(microsecond=0).isoformat())


class CityOrderRuntime(Base):
    __tablename__ = 'city_order_runtime'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    currency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    tariff_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    recommended_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    system_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    from_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    from_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    to_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    to_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_trip_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dispatch_stage: Mapped[str | None] = mapped_column(String(32), nullable=True)
    seen_by_drivers: Mapped[int] = mapped_column(Integer, default=0)
    active_trip_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class CityTripV1(Base):
    __tablename__ = 'city_trips_v1'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(32), default='accepted')
    price: Mapped[float] = mapped_column(Float, default=0.0)
    country: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    from_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seats: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    passenger_tg_id: Mapped[int] = mapped_column(Integer, index=True)
    driver_tg_id: Mapped[int] = mapped_column(Integer, index=True)
    pickup_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    pickup_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    destination_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    destination_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    driver_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    driver_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    passenger_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    passenger_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DriverOnlineState(Base):
    __tablename__ = 'driver_online_state'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_tg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    country: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TariffSetting(Base):
    __tablename__ = 'tariff_settings'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    currency: Mapped[str] = mapped_column(String(16))
    price_per_km: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IntercityRouteV1(Base):
    __tablename__ = 'intercity_routes_v1'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    creator_tg_id: Mapped[int] = mapped_column(Integer, index=True)
    country: Mapped[str | None] = mapped_column(String(32), nullable=True)
    from_city: Mapped[str] = mapped_column(String(255))
    to_city: Mapped[str] = mapped_column(String(255))
    departure_date: Mapped[str] = mapped_column(String(64))
    departure_time: Mapped[str] = mapped_column(String(64))
    seats: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    accepted_by_tg_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default='active')
    created_at: Mapped[str] = mapped_column(String(64), default=lambda: utcnow().replace(microsecond=0).isoformat())


class IntercityRouteMeta(Base):
    __tablename__ = 'intercity_route_meta'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    pickup_mode: Mapped[str] = mapped_column(String(32), default='ask_driver')
    meeting_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    meeting_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    meeting_lng: Mapped[float | None] = mapped_column(Float, nullable=True)


class IntercityRequestV1(Base):
    __tablename__ = 'intercity_requests_v1'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    creator_tg_id: Mapped[int] = mapped_column(Integer, index=True)
    country: Mapped[str | None] = mapped_column(String(32), nullable=True)
    from_city: Mapped[str] = mapped_column(String(255))
    to_city: Mapped[str] = mapped_column(String(255))
    desired_date: Mapped[str] = mapped_column(String(64))
    desired_time: Mapped[str] = mapped_column(String(64))
    seats_needed: Mapped[int] = mapped_column(Integer, default=1)
    price_offer: Mapped[float] = mapped_column(Float, default=0.0)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    accepted_by_tg_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default='active')
    created_at: Mapped[str] = mapped_column(String(64), default=lambda: utcnow().replace(microsecond=0).isoformat())


class ChatMessageV1(Base):
    __tablename__ = 'chat_messages_v1'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_type: Mapped[str] = mapped_column(String(32), index=True)
    trip_id: Mapped[int] = mapped_column(Integer, index=True)
    sender_tg_id: Mapped[int] = mapped_column(Integer, index=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IntercityChatAccess(Base):
    __tablename__ = 'intercity_chat_access'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_type: Mapped[str] = mapped_column(String(32), index=True)
    trip_id: Mapped[int] = mapped_column(Integer, index=True)
    user_tg_id: Mapped[int] = mapped_column(Integer, index=True)
    granted_by_tg_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint('trip_type', 'trip_id', 'user_tg_id', name='uq_intercity_chat_access'),)


def _default_sql(column) -> str | None:
    if column.default is not None and getattr(column.default, "is_scalar", False):
        value = column.default.arg
    elif isinstance(column.type, (Boolean, Integer)):
        value = 0
    elif isinstance(column.type, Float):
        value = 0.0
    elif isinstance(column.type, (String, Text)):
        value = ''
    else:
        return None
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return str(int(value) if isinstance(value, bool) else value)


def _apply_additive_schema_updates(sync_conn) -> None:
    inspector = inspect(sync_conn)
    for table in Base.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue
        existing = {col['name'] for col in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing:
                continue
            type_sql = column.type.compile(dialect=sync_conn.dialect)
            default_sql = _default_sql(column)
            statement = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {type_sql}'
            if default_sql is not None:
                statement += f' DEFAULT {default_sql}'
            if not column.nullable and default_sql is not None:
                statement += ' NOT NULL'
            sync_conn.execute(text(statement))


async def async_main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_apply_additive_schema_updates)
