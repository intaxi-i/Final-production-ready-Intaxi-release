from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException
from sqlalchemy import select

from api.auth import get_current_user
from api.schemas import DriverOnlineStateResponse, DriverOnlineUpdateRequest
from intaxi_bot.app.database.models import CityTripV1, DriverOnlineState, User, async_session, utcnow

LIVE_CITY_STATUSES = {'accepted', 'driver_on_way', 'driver_arrived', 'in_progress'}


def _clean(value: Any) -> str:
    return str(value or '').strip().lower()


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    return value.replace(microsecond=0).isoformat() if hasattr(value, 'replace') and hasattr(value, 'isoformat') else str(value)


async def _driver_has_live_trip(session, driver_tg_id: int) -> bool:
    trip = await session.scalar(
        select(CityTripV1)
        .where(CityTripV1.driver_tg_id == driver_tg_id, CityTripV1.status.in_(list(LIVE_CITY_STATUSES)))
        .order_by(CityTripV1.id.desc())
    )
    return trip is not None


async def strict_driver_online_update(payload: DriverOnlineUpdateRequest, current_user: User = Depends(get_current_user)) -> DriverOnlineStateResponse:
    if not current_user.is_verified or _clean(current_user.active_role) != 'driver':
        raise HTTPException(status_code=403, detail='Only verified drivers in driver mode can go online')
    async with async_session() as session:
        driver = await session.scalar(select(User).where(User.tg_id == current_user.tg_id))
        if not driver or not driver.is_verified or _clean(driver.active_role) != 'driver':
            raise HTTPException(status_code=403, detail='Only verified drivers in driver mode can go online')
        row = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == driver.tg_id))
        if not row:
            row = DriverOnlineState(driver_tg_id=driver.tg_id, is_online=False, country=driver.country, city=driver.city)
            session.add(row)
            await session.flush()
        row.is_online = bool(payload.is_online)
        row.country = _clean(payload.country_code or payload.country or driver.country) or row.country
        row.city = str(payload.city or payload.city_id or driver.city or row.city or '').strip()
        if payload.lat is not None:
            row.lat = payload.lat
        if payload.lng is not None:
            row.lng = payload.lng
        row.updated_at = utcnow()
        busy = await _driver_has_live_trip(session, driver.tg_id)
        await session.commit()
        await session.refresh(row)
        return DriverOnlineStateResponse(
            is_online=bool(row.is_online),
            lat=row.lat,
            lng=row.lng,
            country=row.country,
            city=row.city,
            is_busy=busy,
            updated_at=_iso(row.updated_at),
        )
