from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import or_, select

from intaxi_bot.app.database.models import CityOrderV1, CityTripV1, IntercityRequestV1, IntercityRouteV1

CANONICAL_STATUSES = {
    'active',
    'accepted',
    'in_progress',
    'completed',
    'cancelled',
    'closed',
}

LIVE_CITY_STATUSES = {'accepted', 'driver_on_way', 'driver_arrived', 'in_progress'}
FINAL_CITY_STATUSES = {'completed', 'cancelled', 'closed', 'cancelled_by_admin'}
CITY_STATUS_NEXT = {
    'accepted': {'driver_on_way', 'driver_arrived', 'cancelled'},
    'driver_on_way': {'driver_arrived', 'cancelled'},
    'driver_arrived': {'in_progress', 'cancelled'},
    'in_progress': {'completed', 'cancelled'},
}

FINAL_INTERCITY_STATUSES = {'completed', 'cancelled', 'closed'}
INTERCITY_STATUS_NEXT = {
    'active': {'cancelled', 'closed', 'accepted'},
    'accepted': {'in_progress', 'cancelled', 'closed'},
    'in_progress': {'completed', 'cancelled', 'closed'},
}


@dataclass(frozen=True)
class TripActors:
    creator_tg_id: int | None
    accepted_by_tg_id: int | None
    passenger_tg_id: int | None
    driver_tg_id: int | None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def normalize_completion_or_cancel(status: str) -> str:
    if status == 'cancelled_by_admin':
        return 'cancelled'
    return status


def is_participant(user_tg_id: int, actors: TripActors) -> bool:
    participants = {actors.creator_tg_id, actors.accepted_by_tg_id, actors.passenger_tg_id, actors.driver_tg_id}
    return user_tg_id in participants


def ensure_supported_city_status(new_status: str) -> None:
    if new_status not in LIVE_CITY_STATUSES | FINAL_CITY_STATUSES:
        raise HTTPException(status_code=400, detail='Unsupported city trip status')


def ensure_city_transition_allowed(current_status: str, new_status: str, *, is_driver: bool, is_passenger: bool) -> None:
    if current_status in FINAL_CITY_STATUSES:
        if new_status == current_status:
            return
        raise HTTPException(status_code=409, detail='Trip is already finished')

    if is_driver:
        if new_status != current_status and new_status not in CITY_STATUS_NEXT.get(current_status, set()):
            raise HTTPException(status_code=409, detail='Invalid city trip status transition')
        return
    if is_passenger:
        if new_status != 'cancelled':
            raise HTTPException(status_code=403, detail='Only the driver can update trip progress')
        return
    raise HTTPException(status_code=403, detail='Forbidden')


def ensure_intercity_transition_allowed(current_status: str, new_status: str, *, is_creator: bool, is_accepted_by: bool) -> None:
    if current_status in FINAL_INTERCITY_STATUSES:
        raise HTTPException(status_code=409, detail='Trip is already finished')
    if new_status not in INTERCITY_STATUS_NEXT.get(current_status, set()):
        raise HTTPException(status_code=403, detail='Unsupported status transition')

    if current_status == 'active' and not is_creator:
        raise HTTPException(status_code=403, detail='Unsupported status transition')
    if new_status == 'in_progress' and not is_creator:
        raise HTTPException(status_code=403, detail='Unsupported status transition')
    if new_status == 'completed' and not is_creator:
        raise HTTPException(status_code=403, detail='Unsupported status transition')
    if new_status in {'cancelled', 'closed'} and not (is_creator or is_accepted_by):
        raise HTTPException(status_code=403, detail='Unsupported status transition')


def ensure_participant_or_forbidden(user_tg_id: int, actors: TripActors) -> None:
    if not is_participant(user_tg_id, actors):
        raise HTTPException(status_code=403, detail='Forbidden')


async def find_current_city_trip(session, user_tg_id: int) -> CityTripV1 | None:
    return await session.scalar(
        select(CityTripV1)
        .where(
            or_(CityTripV1.passenger_tg_id == user_tg_id, CityTripV1.driver_tg_id == user_tg_id),
            CityTripV1.status.in_(list(LIVE_CITY_STATUSES)),
        )
        .order_by(CityTripV1.id.desc())
    )


async def find_current_city_order(session, user_tg_id: int) -> CityOrderV1 | None:
    return await session.scalar(
        select(CityOrderV1)
        .where(CityOrderV1.creator_tg_id == user_tg_id, CityOrderV1.status == 'active', CityOrderV1.role == 'passenger')
        .order_by(CityOrderV1.id.desc())
    )


async def find_current_intercity_offer(session, user_tg_id: int) -> tuple[str, Any] | None:
    route = await session.scalar(
        select(IntercityRouteV1)
        .where(
            or_(IntercityRouteV1.creator_tg_id == user_tg_id, IntercityRouteV1.accepted_by_tg_id == user_tg_id),
            IntercityRouteV1.status.in_(['active', 'accepted', 'in_progress']),
        )
        .order_by(IntercityRouteV1.id.desc())
    )
    if route:
        return 'intercity_route', route
    req = await session.scalar(
        select(IntercityRequestV1)
        .where(
            or_(IntercityRequestV1.creator_tg_id == user_tg_id, IntercityRequestV1.accepted_by_tg_id == user_tg_id),
            IntercityRequestV1.status.in_(['active', 'accepted', 'in_progress']),
        )
        .order_by(IntercityRequestV1.id.desc())
    )
    if req:
        return 'intercity_request', req
    return None
