from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException
from sqlalchemy import select

from api.auth import get_current_user
from api.schemas import UpdateProfileRequest, UpdateRoleRequest, UpdateVehicleRequest, UserEnvelope, UserMe, VehicleInfo
from intaxi_bot.app.database.models import (
    CityTripV1,
    DriverOnlineState,
    IntercityRequestV1,
    IntercityRouteV1,
    User,
    Vehicle,
    async_session,
    utcnow,
)
from intaxi_bot.app.database.requests import register_vehicle, set_user_reg

LIVE_CITY_STATUSES = {'accepted', 'driver_on_way', 'driver_arrived', 'in_progress'}
LIVE_INTERCITY_STATUSES = {'accepted', 'in_progress'}


def _clean(value: Any) -> str:
    return str(value or '').strip().lower()


def _vehicle_to_schema(vehicle: Vehicle | None) -> VehicleInfo | None:
    if not vehicle:
        return None
    return VehicleInfo(
        brand=vehicle.brand,
        model=vehicle.model,
        plate=vehicle.plate,
        color=vehicle.color,
        capacity=vehicle.capacity,
        vehicle_class=vehicle.vehicle_class,
    )


async def _to_user_envelope(user: User) -> UserEnvelope:
    async with async_session() as session:
        db_user = await session.scalar(select(User).where(User.tg_id == user.tg_id))
        if not db_user:
            raise HTTPException(status_code=404, detail='User not found')
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == db_user.id))
        return UserEnvelope(user=UserMe(
            tg_id=db_user.tg_id,
            full_name=db_user.full_name,
            username=db_user.username,
            language=db_user.language,
            country=db_user.country,
            city=db_user.city,
            balance=float(db_user.balance or 0),
            commission_due=float(db_user.commission_due or 0),
            free_rides_left=int(getattr(db_user, 'free_rides_left', 0) or 0),
            active_role=db_user.active_role,
            is_verified=bool(db_user.is_verified),
            vehicle=_vehicle_to_schema(vehicle),
        ))


async def _has_live_driver_work(session, tg_id: int) -> bool:
    city_trip = await session.scalar(
        select(CityTripV1)
        .where(CityTripV1.driver_tg_id == tg_id, CityTripV1.status.in_(list(LIVE_CITY_STATUSES)))
        .order_by(CityTripV1.id.desc())
    )
    if city_trip:
        return True
    route = await session.scalar(
        select(IntercityRouteV1)
        .where(IntercityRouteV1.creator_tg_id == tg_id, IntercityRouteV1.status.in_(list(LIVE_INTERCITY_STATUSES)))
        .order_by(IntercityRouteV1.id.desc())
    )
    if route:
        return True
    request = await session.scalar(
        select(IntercityRequestV1)
        .where(IntercityRequestV1.accepted_by_tg_id == tg_id, IntercityRequestV1.status.in_(list(LIVE_INTERCITY_STATUSES)))
        .order_by(IntercityRequestV1.id.desc())
    )
    return request is not None


async def _set_driver_offline(session, tg_id: int) -> None:
    row = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == tg_id).with_for_update())
    if row:
        row.is_online = False
        row.updated_at = utcnow()


async def strict_update_profile(payload: UpdateProfileRequest, current_user: User = Depends(get_current_user)) -> UserEnvelope:
    new_language = payload.language or current_user.language or 'ru'
    new_country = payload.country if payload.country is not None else (current_user.country or '')
    new_city = payload.city if payload.city is not None else (current_user.city or '')
    location_changed = (payload.country is not None and _clean(payload.country) != _clean(current_user.country)) or (payload.city is not None and _clean(payload.city) != _clean(current_user.city))

    await set_user_reg(current_user.tg_id, language=new_language, country=new_country, city=new_city)
    async with async_session() as session:
        refreshed = await session.scalar(select(User).where(User.tg_id == current_user.tg_id).with_for_update())
        if not refreshed:
            raise HTTPException(status_code=404, detail='User not found after update')
        if location_changed:
            await _set_driver_offline(session, refreshed.tg_id)
        await session.commit()
        await session.refresh(refreshed)
    return await _to_user_envelope(refreshed)


async def strict_update_role(payload: UpdateRoleRequest, current_user: User = Depends(get_current_user)) -> UserEnvelope:
    requested_role = _clean(payload.active_role)
    if requested_role not in {'driver', 'passenger'}:
        raise HTTPException(status_code=400, detail='active_role must be driver or passenger')

    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == current_user.tg_id).with_for_update())
        if not user:
            raise HTTPException(status_code=404, detail='User not found')
        if requested_role == 'driver':
            if not user.is_verified:
                raise HTTPException(status_code=403, detail='Only verified drivers can switch to driver mode')
            vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))
            if not vehicle:
                raise HTTPException(status_code=403, detail='Vehicle profile is required to switch to driver mode')
            user.active_role = 'driver'
        else:
            if await _has_live_driver_work(session, user.tg_id):
                raise HTTPException(status_code=409, detail='Finish active driver trip before switching to passenger mode')
            user.active_role = 'passenger'
            await _set_driver_offline(session, user.tg_id)
        await session.commit()
        await session.refresh(user)
    return await _to_user_envelope(user)


async def strict_update_vehicle(payload: UpdateVehicleRequest, current_user: User = Depends(get_current_user)) -> UserEnvelope:
    if not payload.brand or not payload.model or not payload.plate:
        raise HTTPException(status_code=400, detail='brand, model and plate are required')
    vehicle_data = payload.model_dump(exclude_none=True)
    await register_vehicle(current_user.tg_id, vehicle_data)
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == current_user.tg_id).with_for_update())
        if not user:
            raise HTTPException(status_code=404, detail='User not found')
        await _set_driver_offline(session, user.tg_id)
        await session.commit()
        await session.refresh(user)
    return await _to_user_envelope(user)
