from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.country import Country
from app.models.intercity import IntercityRequest, IntercityRoute, IntercityTrip
from app.models.user import User
from app.schemas.intercity import (
    IntercityOfferRead,
    IntercityRequestCreate,
    IntercityRouteCreate,
    IntercityTripRead,
    IntercityTripStatusUpdate,
)
from app.services.intercity_service import IntercityService

router = APIRouter(prefix="/intercity", tags=["intercity"])


def _parse_date(value: str | None):
    if not value:
        return None
    return date.fromisoformat(value)


async def _currency(session: AsyncSession, country_code: str) -> str:
    country = await session.scalar(select(Country).where(Country.code == country_code.lower()))
    return country.currency if country else "USD"


@router.post("/requests", response_model=dict)
async def create_intercity_request(
    payload: IntercityRequestCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    row = await IntercityService().create_request(
        session,
        passenger=current_user,
        mode=payload.mode,
        country_code=payload.country_code,
        from_city_id=payload.from_city_id,
        to_city_id=payload.to_city_id,
        from_text=payload.from_text,
        to_text=payload.to_text,
        ride_date=_parse_date(payload.date),
        ride_time=payload.time,
        seats=payload.seats,
        passenger_price=payload.passenger_price,
        currency=await _currency(session, payload.country_code),
        comment=payload.comment,
    )
    await session.commit()
    await session.refresh(row)
    return {"id": row.id, "status": row.status}


@router.post("/routes", response_model=dict)
async def create_intercity_route(
    payload: IntercityRouteCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    row = await IntercityService().create_route(
        session,
        driver=current_user,
        mode=payload.mode,
        country_code=payload.country_code,
        from_city_id=payload.from_city_id,
        to_city_id=payload.to_city_id,
        from_text=payload.from_text,
        to_text=payload.to_text,
        ride_date=_parse_date(payload.date),
        ride_time=payload.time,
        seats_available=payload.seats_available,
        price_per_seat=payload.price_per_seat,
        currency=await _currency(session, payload.country_code),
        pickup_mode=payload.pickup_mode,
        comment=payload.comment,
    )
    await session.commit()
    await session.refresh(row)
    return {"id": row.id, "status": row.status}


@router.get("/offers", response_model=list[IntercityOfferRead])
async def intercity_offers(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[IntercityOfferRead]:
    requests = (await session.scalars(select(IntercityRequest).where(IntercityRequest.status == "active", IntercityRequest.passenger_user_id != current_user.id).order_by(IntercityRequest.id.desc()).limit(50))).all()
    routes = (await session.scalars(select(IntercityRoute).where(IntercityRoute.status == "active", IntercityRoute.driver_user_id != current_user.id).order_by(IntercityRoute.id.desc()).limit(50))).all()
    result: list[IntercityOfferRead] = []
    for row in requests:
        result.append(IntercityOfferRead(kind="request", id=row.id, mode=row.mode, country_code=row.country_code, from_text=row.from_text, to_text=row.to_text, date=str(row.date) if row.date else None, time=row.time, seats=row.seats, price=float(row.passenger_price), currency=row.currency, status=row.status))
    for row in routes:
        result.append(IntercityOfferRead(kind="route", id=row.id, mode=row.mode, country_code=row.country_code, from_text=row.from_text, to_text=row.to_text, date=str(row.date) if row.date else None, time=row.time, seats=row.seats_available, price=float(row.price_per_seat), currency=row.currency, status=row.status))
    return result


@router.post("/offers/{kind}/{item_id}/accept", response_model=IntercityTripRead)
async def accept_intercity_offer(
    kind: str,
    item_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IntercityTripRead:
    service = IntercityService()
    if kind == "request":
        trip = await service.accept_request(session, request_id=item_id, driver=current_user)
    else:
        trip = await service.accept_route(session, route_id=item_id, passenger=current_user)
    await session.commit()
    await session.refresh(trip)
    return IntercityTripRead.model_validate(trip)


@router.get("/trips/current", response_model=dict)
async def current_intercity_trip(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    trip = await session.scalar(select(IntercityTrip).where(or_(IntercityTrip.passenger_user_id == current_user.id, IntercityTrip.driver_user_id == current_user.id), IntercityTrip.status.in_({"accepted", "driver_on_way", "in_progress"})).order_by(IntercityTrip.id.desc()))
    return {"item": IntercityTripRead.model_validate(trip).model_dump() if trip else None}


@router.post("/trips/{trip_id}/status", response_model=IntercityTripRead)
async def update_intercity_trip_status(
    trip_id: int,
    payload: IntercityTripStatusUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IntercityTripRead:
    from app.core.errors import raise_domain
    trip = await session.scalar(select(IntercityTrip).where(IntercityTrip.id == trip_id))
    if not trip:
        raise_domain("intercity_trip_not_found", "Intercity trip not found", 404)
    if trip.driver_user_id != current_user.id:
        raise_domain("only_driver_can_update_trip", "Only assigned driver can update trip", 403)
    allowed = {
        "accepted": {"driver_on_way", "in_progress", "cancelled", "disputed"},
        "driver_on_way": {"in_progress", "cancelled", "disputed"},
        "in_progress": {"completed", "cancelled", "disputed"},
    }
    if payload.status != trip.status and payload.status not in allowed.get(trip.status, set()):
        raise_domain("invalid_status_transition", "Invalid status transition", 409)
    trip.status = payload.status
    await session.commit()
    await session.refresh(trip)
    return IntercityTripRead.model_validate(trip)
