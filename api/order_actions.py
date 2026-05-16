from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from intaxi_bot.app.database.models import (
    CityOrderRuntime,
    CityOrderV1,
    CityTripV1,
    DriverOnlineState,
    User,
    Vehicle,
    async_session,
)

LIVE_CITY_TRIP_STATUSES = {'accepted', 'driver_on_way', 'driver_arrived', 'in_progress'}
FINAL_CITY_TRIP_STATUSES = {'completed', 'cancelled', 'closed', 'cancelled_by_admin'}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _clean(value: Any) -> str:
    return str(value or '').strip().lower()


def _same_or_empty(left: Any, right: Any) -> bool:
    left_value = _clean(left)
    right_value = _clean(right)
    return not left_value or not right_value or left_value == right_value


async def _driver_has_live_trip(session, driver_tg_id: int) -> bool:
    trip = await session.scalar(
        select(CityTripV1)
        .where(CityTripV1.driver_tg_id == driver_tg_id, CityTripV1.status.in_(list(LIVE_CITY_TRIP_STATUSES)))
        .order_by(CityTripV1.id.desc())
    )
    return trip is not None


async def close_city_order_for_user(order_id: int, tg_id: int) -> CityOrderV1 | None:
    async with async_session() as session:
        row = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id, CityOrderV1.creator_tg_id == tg_id).with_for_update())
        if not row:
            return None
        row.status = 'closed'
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == row.id).with_for_update())
        if runtime and runtime.active_trip_id:
            trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == runtime.active_trip_id).with_for_update())
            if trip and trip.status not in FINAL_CITY_TRIP_STATUSES:
                trip.status = 'cancelled'
                trip.cancelled_at = _now()
                trip.updated_at = _now()
            runtime.active_trip_id = None
        await session.commit()
        await session.refresh(row)
        return row


async def accept_city_offer_for_user(order_id: int, tg_id: int) -> CityTripV1 | None:
    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id).with_for_update())
        accepter = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not order or not accepter or order.status != 'active' or order.creator_tg_id == tg_id:
            return None
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id).with_for_update())
        if runtime and runtime.active_trip_id:
            existing = await session.scalar(select(CityTripV1).where(CityTripV1.id == runtime.active_trip_id))
            return existing

        driver_state = None
        if order.role == 'passenger':
            if not accepter.is_verified or _clean(accepter.active_role) != 'driver':
                return None
            vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == accepter.id))
            if not vehicle:
                return None
            driver_state = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == accepter.tg_id))
            if not driver_state or not driver_state.is_online:
                return None
            if not _same_or_empty(driver_state.country, order.country) or not _same_or_empty(driver_state.city, order.city):
                return None
            if await _driver_has_live_trip(session, accepter.tg_id):
                return None
            passenger_tg_id = order.creator_tg_id
            driver_tg_id = accepter.tg_id
        elif order.role == 'driver':
            if _clean(accepter.active_role) == 'driver':
                return None
            driver = await session.scalar(select(User).where(User.tg_id == order.creator_tg_id))
            if not driver or not driver.is_verified:
                return None
            vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == driver.id))
            if not vehicle:
                return None
            if not _same_or_empty(accepter.country, order.country) or not _same_or_empty(accepter.city, order.city):
                return None
            passenger_tg_id = accepter.tg_id
            driver_tg_id = order.creator_tg_id
        else:
            return None

        trip = CityTripV1(
            order_id=order.id,
            status='accepted',
            price=float(order.price or 0),
            country=order.country,
            city=order.city,
            from_address=order.from_address,
            to_address=order.to_address,
            seats=order.seats,
            comment=order.comment,
            passenger_tg_id=passenger_tg_id,
            driver_tg_id=driver_tg_id,
            pickup_lat=runtime.from_lat if runtime else None,
            pickup_lng=runtime.from_lng if runtime else None,
            destination_lat=runtime.to_lat if runtime else None,
            destination_lng=runtime.to_lng if runtime else None,
            passenger_lat=runtime.from_lat if runtime else None,
            passenger_lng=runtime.from_lng if runtime else None,
            driver_lat=driver_state.lat if driver_state else None,
            driver_lng=driver_state.lng if driver_state else None,
        )
        session.add(trip)
        await session.flush()
        order.accepted_by_tg_id = tg_id
        order.status = 'accepted'
        if runtime:
            runtime.active_trip_id = trip.id
        await session.commit()
        await session.refresh(trip)
        return trip


async def update_city_order_status_for_user(order_id: int, tg_id: int, status: str) -> CityOrderV1 | None:
    if status in {'closed', 'cancelled'}:
        row = await close_city_order_for_user(order_id, tg_id)
        if row and status == 'cancelled':
            async with async_session() as session:
                db_row = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == row.id, CityOrderV1.creator_tg_id == tg_id).with_for_update())
                if not db_row:
                    return row
                db_row.status = 'cancelled'
                await session.commit()
                await session.refresh(db_row)
                return db_row
        return row
    return None
