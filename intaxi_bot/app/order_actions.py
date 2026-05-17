from __future__ import annotations

from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Any

from sqlalchemy import select

from app.database.models import (
    CityOrderRuntime,
    CityOrderV1,
    CityTripV1,
    DriverOnlineState,
    IntercityChatAccess,
    IntercityRequestV1,
    IntercityRouteV1,
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


def _city_matches(user_city: Any, row_city: Any) -> bool:
    user_value = _clean(user_city)
    row_value = _clean(row_city)
    if not user_value or not row_value:
        return True
    return user_value == row_value or user_value in row_value or row_value in user_value


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return radius * 2 * asin(sqrt(a))


def _distance_from_state(runtime: CityOrderRuntime | None, state: DriverOnlineState | None) -> float | None:
    if not runtime or not state:
        return None
    if runtime.from_lat is None or runtime.from_lng is None or state.lat is None or state.lng is None:
        return None
    return round(_haversine_km(float(runtime.from_lat), float(runtime.from_lng), float(state.lat), float(state.lng)), 2)


async def _driver_has_live_trip(session, driver_tg_id: int) -> bool:
    trip = await session.scalar(
        select(CityTripV1)
        .where(CityTripV1.driver_tg_id == driver_tg_id, CityTripV1.status.in_(list(LIVE_CITY_TRIP_STATUSES)))
        .order_by(CityTripV1.id.desc())
    )
    return trip is not None


async def _grant_intercity_chat_access(session, *, trip_type: str, trip_id: int, user_ids: list[int], granted_by_tg_id: int | None) -> None:
    for user_id in dict.fromkeys([u for u in user_ids if u]):
        existing = await session.scalar(
            select(IntercityChatAccess).where(
                IntercityChatAccess.trip_type == trip_type,
                IntercityChatAccess.trip_id == trip_id,
                IntercityChatAccess.user_tg_id == user_id,
            )
        )
        if existing:
            continue
        session.add(
            IntercityChatAccess(
                trip_type=trip_type,
                trip_id=trip_id,
                user_tg_id=user_id,
                granted_by_tg_id=granted_by_tg_id,
            )
        )


async def close_city_order_for_user(order_id: int, tg_id: int) -> CityOrderV1 | None:
    async with async_session() as session:
        order = await session.scalar(
            select(CityOrderV1).where(CityOrderV1.id == order_id, CityOrderV1.creator_tg_id == tg_id).with_for_update()
        )
        if not order:
            return None
        order.status = 'closed'
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id).with_for_update())
        if runtime and runtime.active_trip_id:
            trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == runtime.active_trip_id).with_for_update())
            if trip and trip.status not in FINAL_CITY_TRIP_STATUSES:
                trip.status = 'cancelled'
                trip.cancelled_at = _now()
                trip.updated_at = _now()
            runtime.active_trip_id = None
        await session.commit()
        await session.refresh(order)
        return order


async def list_city_market_for_user(tg_id: int, *, wanted_role: str, limit: int = 10) -> list[dict[str, Any]]:
    async with async_session() as session:
        current_user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not current_user:
            return []

        driver_state = None
        if wanted_role == 'passenger':
            if not current_user.is_verified or _clean(current_user.active_role) != 'driver':
                return []
            driver_vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == current_user.id))
            if not driver_vehicle:
                return []
            driver_state = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == current_user.tg_id))
            if not driver_state or not driver_state.is_online:
                return []
            if await _driver_has_live_trip(session, current_user.tg_id):
                return []
        elif wanted_role == 'driver':
            if _clean(current_user.active_role) == 'driver':
                return []
        else:
            return []

        rows = (
            await session.scalars(
                select(CityOrderV1)
                .where(CityOrderV1.status == 'active', CityOrderV1.role == wanted_role, CityOrderV1.creator_tg_id != tg_id)
                .order_by(CityOrderV1.id.desc())
                .limit(limit * 5)
            )
        ).all()

        result: list[dict[str, Any]] = []
        for row in rows:
            if wanted_role == 'passenger':
                if not _same_or_empty(row.country, driver_state.country) or not _same_or_empty(row.city, driver_state.city):
                    continue
            elif wanted_role == 'driver':
                if not _same_or_empty(row.country, current_user.country) or not _same_or_empty(row.city, current_user.city):
                    continue
            runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == row.id))
            creator = await session.scalar(select(User).where(User.tg_id == row.creator_tg_id))
            vehicle = None
            if row.role == 'driver' and creator:
                if not creator.is_verified:
                    continue
                vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == creator.id))
                if not vehicle:
                    continue
            distance = _distance_from_state(runtime, driver_state)
            result.append({'order': row, 'runtime': runtime, 'creator': creator, 'vehicle': vehicle, 'driver_distance_km': distance})
            if len(result) >= limit:
                break
        result.sort(key=lambda item: (item.get('driver_distance_km') is None, item.get('driver_distance_km') or 10**9, -int(item['order'].id)))
        return result[:limit]


async def accept_city_offer_for_user(order_id: int, tg_id: int) -> CityTripV1 | None:
    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id).with_for_update())
        accepter = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not order or not accepter or order.status != 'active' or order.creator_tg_id == tg_id:
            return None
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id).with_for_update())
        if runtime and runtime.active_trip_id:
            existing = await session.scalar(select(CityTripV1).where(CityTripV1.id == runtime.active_trip_id))
            if existing:
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
            pickup_lat=(runtime.from_lat if runtime else None),
            pickup_lng=(runtime.from_lng if runtime else None),
            destination_lat=(runtime.to_lat if runtime else None),
            destination_lng=(runtime.to_lng if runtime else None),
            passenger_lat=(runtime.from_lat if runtime else None),
            passenger_lng=(runtime.from_lng if runtime else None),
            driver_lat=(driver_state.lat if driver_state else None),
            driver_lng=(driver_state.lng if driver_state else None),
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


async def list_intercity_market_for_user(tg_id: int, *, kind: str, limit: int = 10) -> list[Any]:
    async with async_session() as session:
        current_user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not current_user:
            return []
        country = _clean(current_user.country)
        city = current_user.city

        if kind == 'route':
            if _clean(current_user.active_role) == 'driver':
                return []
            query = select(IntercityRouteV1).where(
                IntercityRouteV1.status == 'active',
                IntercityRouteV1.creator_tg_id != tg_id,
            )
            if country:
                query = query.where(IntercityRouteV1.country == country)
            rows = (await session.scalars(query.order_by(IntercityRouteV1.id.desc()).limit(limit * 5))).all()
            result = []
            for row in rows:
                if not _city_matches(city, row.from_city):
                    continue
                driver = await session.scalar(select(User).where(User.tg_id == row.creator_tg_id))
                if not driver or not driver.is_verified:
                    continue
                result.append(row)
                if len(result) >= limit:
                    break
            return result

        if kind == 'request':
            if not current_user.is_verified or _clean(current_user.active_role) != 'driver':
                return []
            query = select(IntercityRequestV1).where(
                IntercityRequestV1.status == 'active',
                IntercityRequestV1.creator_tg_id != tg_id,
            )
            if country:
                query = query.where(IntercityRequestV1.country == country)
            rows = (await session.scalars(query.order_by(IntercityRequestV1.id.desc()).limit(limit * 5))).all()
            result = []
            for row in rows:
                if not _city_matches(city, row.from_city):
                    continue
                result.append(row)
                if len(result) >= limit:
                    break
            return result

        return []


async def accept_intercity_offer_for_user(*, kind: str, item_id: int, tg_id: int):
    async with async_session() as session:
        current_user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not current_user:
            return None
        if kind == 'route':
            row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == item_id).with_for_update())
            if not row or row.creator_tg_id == tg_id or row.status != 'active':
                return None
            if _clean(current_user.active_role) == 'driver':
                return None
            if not _same_or_empty(current_user.country, row.country) or not _city_matches(current_user.city, row.from_city):
                return None
            driver = await session.scalar(select(User).where(User.tg_id == row.creator_tg_id))
            if not driver or not driver.is_verified:
                return None
            row.accepted_by_tg_id = tg_id
            row.status = 'accepted'
            await _grant_intercity_chat_access(session, trip_type='intercity_route', trip_id=row.id, user_ids=[row.creator_tg_id, tg_id], granted_by_tg_id=tg_id)
            await session.commit()
            await session.refresh(row)
            return row

        if kind == 'request':
            row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == item_id).with_for_update())
            if not row or row.creator_tg_id == tg_id or row.status != 'active':
                return None
            if not current_user.is_verified or _clean(current_user.active_role) != 'driver':
                return None
            if not _same_or_empty(current_user.country, row.country) or not _city_matches(current_user.city, row.from_city):
                return None
            row.accepted_by_tg_id = tg_id
            row.status = 'accepted'
            await _grant_intercity_chat_access(session, trip_type='intercity_request', trip_id=row.id, user_ids=[row.creator_tg_id, tg_id], granted_by_tg_id=tg_id)
            await session.commit()
            await session.refresh(row)
            return row

        return None
