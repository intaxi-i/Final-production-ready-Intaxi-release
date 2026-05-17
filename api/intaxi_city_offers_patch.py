from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any

from fastapi import Depends, Query
from sqlalchemy import select

from api.auth import get_current_user
from api.schemas import CityOrderListResponse
from intaxi_bot.app.database.models import (
    CityOrderRuntime,
    CityOrderV1,
    CityTripV1,
    DriverOnlineState,
    User,
    Vehicle,
    async_session,
)

LIVE_CITY_STATUSES = {'accepted', 'driver_on_way', 'driver_arrived', 'in_progress'}


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    return value.replace(microsecond=0).isoformat() if hasattr(value, 'replace') and hasattr(value, 'isoformat') else str(value)


def _clean(value: Any) -> str:
    return str(value or '').strip().lower()


def _same_or_empty(left: Any, right: Any) -> bool:
    left_value = _clean(left)
    right_value = _clean(right)
    return not left_value or not right_value or left_value == right_value


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return radius * 2 * asin(sqrt(a))


def _vehicle_dict(vehicle: Vehicle | None) -> dict | None:
    if not vehicle:
        return None
    return {
        'brand': vehicle.brand,
        'model': vehicle.model,
        'plate': vehicle.plate,
        'color': vehicle.color,
        'capacity': vehicle.capacity,
        'vehicle_class': vehicle.vehicle_class,
    }


async def _driver_has_live_trip(session, driver_tg_id: int) -> bool:
    trip = await session.scalar(
        select(CityTripV1)
        .where(CityTripV1.driver_tg_id == driver_tg_id, CityTripV1.status.in_(list(LIVE_CITY_STATUSES)))
        .order_by(CityTripV1.id.desc())
    )
    return trip is not None


async def _city_order_item(session, row: CityOrderV1, current_user: User, driver_state: DriverOnlineState | None = None) -> dict | None:
    runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == row.id))
    creator = await session.scalar(select(User).where(User.tg_id == row.creator_tg_id))
    if not creator:
        return None
    vehicle = None
    if row.role == 'driver':
        if not creator.is_verified:
            return None
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == creator.id))
        if not vehicle:
            return None
    distance = None
    eta = None
    if driver_state and runtime and runtime.from_lat is not None and runtime.from_lng is not None and driver_state.lat is not None and driver_state.lng is not None:
        distance = round(_haversine_km(float(runtime.from_lat), float(runtime.from_lng), float(driver_state.lat), float(driver_state.lng)), 2)
        eta = max(2, int(distance / 0.45))
    return {
        'id': row.id,
        'creator_tg_id': row.creator_tg_id,
        'creator_name': creator.full_name,
        'creator_rating': float(creator.rating or 0),
        'role': row.role,
        'country': row.country,
        'city': row.city or '',
        'from_address': row.from_address or '',
        'to_address': row.to_address,
        'seats': int(row.seats or 1),
        'price': float(row.price or 0),
        'recommended_price': float(runtime.recommended_price) if runtime and runtime.recommended_price is not None else None,
        'seen_by_drivers': int(runtime.seen_by_drivers) if runtime else None,
        'can_raise_price_after': 30,
        'estimated_distance_km': float(runtime.estimated_distance_km) if runtime and runtime.estimated_distance_km is not None else None,
        'estimated_trip_min': int(runtime.estimated_trip_min) if runtime and runtime.estimated_trip_min is not None else None,
        'driver_distance_km': distance,
        'driver_eta_min': eta,
        'comment': row.comment,
        'status': row.status,
        'created_at': _iso(row.created_at),
        'is_mine': current_user.tg_id == row.creator_tg_id,
        'active_trip_id': int(runtime.active_trip_id) if runtime and runtime.active_trip_id is not None else None,
        'vehicle': _vehicle_dict(vehicle),
        'currency': runtime.currency if runtime else None,
        'tariff_hint': runtime.tariff_hint if runtime else None,
    }


async def strict_city_offers(kind: str = Query('all'), current_user: User = Depends(get_current_user)) -> CityOrderListResponse:
    async with async_session() as session:
        driver_mode = bool(current_user.is_verified and _clean(current_user.active_role) == 'driver')
        driver_state = None
        if driver_mode:
            driver_vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == current_user.id))
            if not driver_vehicle:
                return CityOrderListResponse(items=[])
            driver_state = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == current_user.tg_id))
            if not driver_state or not driver_state.is_online or await _driver_has_live_trip(session, current_user.tg_id):
                return CityOrderListResponse(items=[])
            wanted_role = 'passenger'
        else:
            wanted_role = 'driver'

        if kind in {'driver', 'passenger'} and kind != wanted_role:
            return CityOrderListResponse(items=[])

        rows = (await session.scalars(
            select(CityOrderV1)
            .where(CityOrderV1.status == 'active', CityOrderV1.role == wanted_role, CityOrderV1.creator_tg_id != current_user.tg_id)
            .order_by(CityOrderV1.id.desc())
            .limit(100)
        )).all()
        items = []
        for row in rows:
            if driver_mode:
                if not _same_or_empty(row.country, driver_state.country) or not _same_or_empty(row.city, driver_state.city):
                    continue
            else:
                if not _same_or_empty(row.country, current_user.country) or not _same_or_empty(row.city, current_user.city):
                    continue
            item = await _city_order_item(session, row, current_user, driver_state)
            if item:
                items.append(item)
    return CityOrderListResponse(items=items)
