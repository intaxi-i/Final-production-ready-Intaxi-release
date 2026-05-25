from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import or_, select

from api.schemas import IntercityOfferResponse, IntercityOwnRouteResponse
from intaxi_bot.app.database.models import IntercityChatAccess, IntercityRequestV1, IntercityRouteMeta, IntercityRouteV1, User

ACTIVE_INTERCITY_STATUSES = {'active', 'accepted', 'in_progress'}
ALL_INTERCITY_STATUSES = ACTIVE_INTERCITY_STATUSES | {'completed', 'cancelled', 'closed'}
ALLOWED_ROUTE_TRANSITIONS = {
    'active': {'accepted', 'cancelled', 'closed'},
    'accepted': {'in_progress', 'completed', 'cancelled', 'closed'},
    'in_progress': {'completed', 'cancelled'},
    'completed': set(),
    'cancelled': set(),
    'closed': set(),
}


def validate_intercity_status(status: str) -> None:
    if status not in ALL_INTERCITY_STATUSES:
        raise HTTPException(status_code=400, detail='Unsupported status')


def validate_transition(current_status: str, next_status: str) -> None:
    if current_status == next_status:
        return
    allowed = ALLOWED_ROUTE_TRANSITIONS.get(current_status, set())
    if next_status not in allowed:
        raise HTTPException(status_code=409, detail=f'Invalid status transition: {current_status} -> {next_status}')


def to_iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.replace(microsecond=0).isoformat() if hasattr(value, 'replace') else str(value)


def map_urls(country: str | None, lat: float | None, lng: float | None):
    if lat is None or lng is None:
        return ('google', None, None)
    return ('google', f'https://maps.google.com/maps?q={lat},{lng}&z=14&output=embed', f'https://maps.google.com/?q={lat},{lng}')


async def ensure_chat_access(session, current_user: User, trip_type: str, trip_id: int) -> None:
    if trip_type == 'intercity_route':
        trip = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == trip_id))
        if not trip:
            raise HTTPException(status_code=404, detail='Route not found')
        if current_user.tg_id in {trip.creator_tg_id, trip.accepted_by_tg_id}:
            return
    elif trip_type == 'intercity_request':
        trip = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == trip_id))
        if not trip:
            raise HTTPException(status_code=404, detail='Request not found')
        if current_user.tg_id in {trip.creator_tg_id, trip.accepted_by_tg_id}:
            return
    else:
        return

    access = await session.scalar(select(IntercityChatAccess).where(IntercityChatAccess.trip_type == trip_type, IntercityChatAccess.trip_id == trip_id, IntercityChatAccess.user_tg_id == current_user.tg_id))
    if not access:
        raise HTTPException(status_code=403, detail='Chat access is not granted')


async def grant_intercity_chat_access(session, *, trip_type: str, trip_id: int, current_user: User) -> None:
    if trip_type == 'intercity_route':
        row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == trip_id))
        if not row:
            raise HTTPException(status_code=404, detail='Route not found')
        if current_user.tg_id in {row.creator_tg_id, row.accepted_by_tg_id}:
            return
        meta = await session.scalar(select(IntercityRouteMeta).where(IntercityRouteMeta.route_id == row.id))
        if meta and (meta.pickup_mode or 'ask_driver') != 'ask_driver':
            raise HTTPException(status_code=403, detail='Chat is disabled for this route')
    elif trip_type == 'intercity_request':
        row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == trip_id))
        if not row:
            raise HTTPException(status_code=404, detail='Request not found')
        if current_user.tg_id in {row.creator_tg_id, row.accepted_by_tg_id}:
            return
    else:
        raise HTTPException(status_code=400, detail='Unsupported intercity object type')
    if row.status not in ACTIVE_INTERCITY_STATUSES:
        raise HTTPException(status_code=403, detail='Chat is not available for closed items')
    access = await session.scalar(select(IntercityChatAccess).where(IntercityChatAccess.trip_type == trip_type, IntercityChatAccess.trip_id == trip_id, IntercityChatAccess.user_tg_id == current_user.tg_id))
    if not access:
        session.add(IntercityChatAccess(trip_type=trip_type, trip_id=trip_id, user_tg_id=current_user.tg_id, granted_by_tg_id=row.creator_tg_id))


async def offer_from_route(session, route: IntercityRouteV1, current_user: User | None = None) -> IntercityOfferResponse:
    creator = await session.scalar(select(User).where(User.tg_id == route.creator_tg_id))
    meta = await session.scalar(select(IntercityRouteMeta).where(IntercityRouteMeta.route_id == route.id))
    provider, embed, action = map_urls(route.country, meta.meeting_lat if meta else None, meta.meeting_lng if meta else None)
    return IntercityOfferResponse(kind='route', id=route.id, creator_tg_id=route.creator_tg_id, creator_name=creator.full_name if creator else None, country=route.country, from_city=route.from_city, to_city=route.to_city, date=route.departure_date, time=route.departure_time, seats=route.seats, price=float(route.price or 0), comment=route.comment, status=route.status, created_at=to_iso(route.created_at), is_mine=bool(current_user and current_user.tg_id == route.creator_tg_id), pickup_mode=meta.pickup_mode if meta else 'ask_driver', active_trip_id=route.id if route.status in ACTIVE_INTERCITY_STATUSES - {'active'} else None, accepted_by_tg_id=route.accepted_by_tg_id, can_accept=bool(current_user and current_user.tg_id not in {route.creator_tg_id, route.accepted_by_tg_id} and route.status == 'active'), map_provider=provider, map_embed_url=embed, map_action_url=action)


async def own_route_item(session, row: IntercityRouteV1) -> IntercityOwnRouteResponse:
    meta = await session.scalar(select(IntercityRouteMeta).where(IntercityRouteMeta.route_id == row.id))
    return IntercityOwnRouteResponse(id=row.id, country=row.country, from_city=row.from_city, to_city=row.to_city, date=row.departure_date, time=row.departure_time, seats=row.seats, price=row.price, comment=row.comment, status=row.status, created_at=to_iso(row.created_at), pickup_mode=meta.pickup_mode if meta else 'ask_driver')


async def offer_from_request(session, req: IntercityRequestV1, current_user: User | None = None) -> IntercityOfferResponse:
    creator = await session.scalar(select(User).where(User.tg_id == req.creator_tg_id))
    provider, embed, action = map_urls(req.country, None, None)
    return IntercityOfferResponse(
        kind='request', id=req.id, creator_tg_id=req.creator_tg_id, creator_name=creator.full_name if creator else None,
        country=req.country, from_city=req.from_city, to_city=req.to_city, date=req.desired_date, time=req.desired_time,
        seats=req.seats_needed, price=float(req.price_offer or 0), comment=req.comment, status=req.status, created_at=to_iso(req.created_at),
        is_mine=bool(current_user and current_user.tg_id == req.creator_tg_id), pickup_mode='ask_driver',
        active_trip_id=req.id if req.status in {'accepted', 'in_progress'} else None,
        accepted_by_tg_id=req.accepted_by_tg_id,
        can_accept=bool(current_user and current_user.tg_id not in {req.creator_tg_id, req.accepted_by_tg_id} and req.status == 'active'),
        map_provider=provider, map_embed_url=embed, map_action_url=action,
    )
