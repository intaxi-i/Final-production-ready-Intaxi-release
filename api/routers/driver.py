from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from api.auth import get_current_user
from api.schemas import (
    DriverLocationUpdateRequest,
    DriverOnlineStateResponse,
    DriverOnlineUpdateRequest,
)
from intaxi_bot.app.database.models import (
    CityTripV1,
    DriverOnlineState,
    User,
    async_session,
    utcnow,
)

router = APIRouter(prefix="/driver", tags=["driver"])


async def _require_verified_driver(current_user: User, *, detail: str = "Only verified drivers can use this feature") -> None:
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail=detail)


async def _ensure_online_state(session, driver: User) -> DriverOnlineState:
    row = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == driver.tg_id))
    if not row:
        row = DriverOnlineState(
            driver_tg_id=driver.tg_id,
            is_online=False,
            country=driver.country,
            city=driver.city,
        )
        session.add(row)
        await session.flush()
    return row


@router.get("/online", response_model=DriverOnlineStateResponse)
async def driver_online_state(current_user: User = Depends(get_current_user)) -> DriverOnlineStateResponse:
    await _require_verified_driver(current_user)
    async with async_session() as session:
        row = await _ensure_online_state(session, current_user)
        await session.commit()
        return DriverOnlineStateResponse(
            is_online=bool(row.is_online),
            lat=row.lat,
            lng=row.lng,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )


@router.post("/online", response_model=DriverOnlineStateResponse)
async def driver_online_update(
    payload: DriverOnlineUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> DriverOnlineStateResponse:
    await _require_verified_driver(current_user)
    async with async_session() as session:
        row = await _ensure_online_state(session, current_user)
        row.is_online = bool(payload.is_online)
        row.country = payload.country or current_user.country
        row.city = payload.city or current_user.city
        if payload.lat is not None:
            row.lat = payload.lat
        if payload.lng is not None:
            row.lng = payload.lng
        row.updated_at = utcnow()
        await session.commit()
        return DriverOnlineStateResponse(
            is_online=bool(row.is_online),
            lat=row.lat,
            lng=row.lng,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )


@router.post("/location")
async def driver_location_update(
    payload: DriverLocationUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    await _require_verified_driver(current_user)
    async with async_session() as session:
        row = await _ensure_online_state(session, current_user)
        row.lat = payload.lat
        row.lng = payload.lng
        row.updated_at = utcnow()
        if payload.trip_id:
            trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == payload.trip_id))
            if trip and trip.driver_tg_id == current_user.tg_id:
                trip.driver_lat = payload.lat
                trip.driver_lng = payload.lng
        await session.commit()
    return {"status": "ok"}
