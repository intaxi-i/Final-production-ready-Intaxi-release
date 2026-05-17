from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select

from api.auth import get_current_user
from api.schemas import IntercityAcceptResponse, IntercityOfferEnvelope, IntercityOfferListResponse, IntercityOfferResponse
from intaxi_bot.app.database.models import (
    IntercityChatAccess,
    IntercityRequestV1,
    IntercityRouteMeta,
    IntercityRouteV1,
    User,
    async_session,
)

ACTIVE_STATUSES = {'active'}


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


def _driver_mode(user: User) -> bool:
    return bool(user.is_verified and _clean(user.active_role) == 'driver')


def _map_provider(country: str | None) -> str:
    return 'yandex' if country in {'uz', 'tr'} else 'google'


def _map_urls(country: str | None, lat: float | None = None, lng: float | None = None):
    provider = _map_provider(country)
    if lat is None or lng is None:
        return provider, None, None
    if provider == 'yandex':
        return provider, f'https://yandex.com/map-widget/v1/?ll={lng}%2C{lat}&z=12&pt={lng},{lat},pm2rdm', f'https://yandex.com/maps/?ll={lng},{lat}&z=12&pt={lng},{lat},pm2rdm'
    query = f'{lat},{lng}'
    return provider, f'https://maps.google.com/maps?q={query}&z=12&output=embed', f'https://www.google.com/maps?q={query}'


async def _grant_chat_access(session, *, trip_type: str, trip_id: int, user_ids: list[int], granted_by_tg_id: int | None) -> None:
    for user_id in dict.fromkeys([u for u in user_ids if u]):
        exists = await session.scalar(
            select(IntercityChatAccess).where(
                IntercityChatAccess.trip_type == trip_type,
                IntercityChatAccess.trip_id == trip_id,
                IntercityChatAccess.user_tg_id == user_id,
            )
        )
        if exists:
            continue
        session.add(
            IntercityChatAccess(
                trip_type=trip_type,
                trip_id=trip_id,
                user_tg_id=user_id,
                granted_by_tg_id=granted_by_tg_id,
            )
        )


async def _route_response(session, row: IntercityRouteV1, current_user: User) -> IntercityOfferResponse:
    creator = await session.scalar(select(User).where(User.tg_id == row.creator_tg_id))
    meta = await session.scalar(select(IntercityRouteMeta).where(IntercityRouteMeta.route_id == row.id))
    provider, embed, action = _map_urls(row.country, meta.meeting_lat if meta else None, meta.meeting_lng if meta else None)
    return IntercityOfferResponse(
        kind='route',
        id=row.id,
        creator_tg_id=row.creator_tg_id,
        creator_name=creator.full_name if creator else None,
        country=row.country,
        from_city=row.from_city or '',
        to_city=row.to_city or '',
        date=row.departure_date or '',
        time=row.departure_time or '',
        seats=int(row.seats or 1),
        price=float(row.price or 0),
        comment=row.comment,
        status=row.status,
        created_at=str(row.created_at) if row.created_at else None,
        is_mine=current_user.tg_id == row.creator_tg_id,
        pickup_mode=meta.pickup_mode if meta else 'ask_driver',
        accepted_by_tg_id=row.accepted_by_tg_id,
        can_accept=(not _driver_mode(current_user) and current_user.tg_id != row.creator_tg_id and row.status == 'active'),
        map_provider=provider,
        map_embed_url=embed,
        map_action_url=action,
    )


async def _request_response(session, row: IntercityRequestV1, current_user: User) -> IntercityOfferResponse:
    creator = await session.scalar(select(User).where(User.tg_id == row.creator_tg_id))
    provider, embed, action = _map_urls(row.country)
    return IntercityOfferResponse(
        kind='request',
        id=row.id,
        creator_tg_id=row.creator_tg_id,
        creator_name=creator.full_name if creator else None,
        country=row.country,
        from_city=row.from_city or '',
        to_city=row.to_city or '',
        date=row.desired_date or '',
        time=row.desired_time or '',
        seats=int(row.seats_needed or 1),
        price=float(row.price_offer or 0),
        comment=row.comment,
        status=row.status,
        created_at=str(row.created_at) if row.created_at else None,
        is_mine=current_user.tg_id == row.creator_tg_id,
        accepted_by_tg_id=row.accepted_by_tg_id,
        can_accept=(_driver_mode(current_user) and current_user.tg_id != row.creator_tg_id and row.status == 'active'),
        map_provider=provider,
        map_embed_url=embed,
        map_action_url=action,
    )


async def _eligible_route(session, row: IntercityRouteV1 | None, current_user: User) -> bool:
    if not row or row.status not in ACTIVE_STATUSES or row.creator_tg_id == current_user.tg_id:
        return False
    if _driver_mode(current_user):
        return False
    if not _same_or_empty(current_user.country, row.country) or not _city_matches(current_user.city, row.from_city):
        return False
    driver = await session.scalar(select(User).where(User.tg_id == row.creator_tg_id))
    return bool(driver and driver.is_verified)


async def _eligible_request(row: IntercityRequestV1 | None, current_user: User) -> bool:
    if not row or row.status not in ACTIVE_STATUSES or row.creator_tg_id == current_user.tg_id:
        return False
    if not _driver_mode(current_user):
        return False
    return bool(_same_or_empty(current_user.country, row.country) and _city_matches(current_user.city, row.from_city))


async def safe_intercity_offers(current_user: User = Depends(get_current_user)) -> IntercityOfferListResponse:
    async with async_session() as session:
        items = []
        if _driver_mode(current_user):
            rows = (await session.scalars(select(IntercityRequestV1).where(IntercityRequestV1.status == 'active', IntercityRequestV1.creator_tg_id != current_user.tg_id).order_by(IntercityRequestV1.id.desc()).limit(100))).all()
            for row in rows:
                if await _eligible_request(row, current_user):
                    items.append(await _request_response(session, row, current_user))
        else:
            rows = (await session.scalars(select(IntercityRouteV1).where(IntercityRouteV1.status == 'active', IntercityRouteV1.creator_tg_id != current_user.tg_id).order_by(IntercityRouteV1.id.desc()).limit(100))).all()
            for row in rows:
                if await _eligible_route(session, row, current_user):
                    items.append(await _route_response(session, row, current_user))
    return IntercityOfferListResponse(items=items)


async def safe_intercity_offer_detail(kind: str, item_id: int, current_user: User = Depends(get_current_user)) -> IntercityOfferEnvelope:
    async with async_session() as session:
        if kind == 'route':
            row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == item_id))
            if not row:
                raise HTTPException(status_code=404, detail='Route not found')
            allowed = current_user.tg_id in {row.creator_tg_id, row.accepted_by_tg_id} or await _eligible_route(session, row, current_user)
            if not allowed:
                raise HTTPException(status_code=403, detail='Forbidden')
            return IntercityOfferEnvelope(item=await _route_response(session, row, current_user))
        if kind == 'request':
            row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == item_id))
            if not row:
                raise HTTPException(status_code=404, detail='Request not found')
            allowed = current_user.tg_id in {row.creator_tg_id, row.accepted_by_tg_id} or await _eligible_request(row, current_user)
            if not allowed:
                raise HTTPException(status_code=403, detail='Forbidden')
            return IntercityOfferEnvelope(item=await _request_response(session, row, current_user))
    raise HTTPException(status_code=400, detail='Unsupported intercity kind')


async def safe_intercity_accept(kind: str, item_id: int, current_user: User = Depends(get_current_user)) -> IntercityAcceptResponse:
    async with async_session() as session:
        if kind == 'route':
            row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == item_id).with_for_update())
            if not await _eligible_route(session, row, current_user):
                raise HTTPException(status_code=403, detail='Route is not available for acceptance')
            if row.accepted_by_tg_id and row.accepted_by_tg_id != current_user.tg_id:
                raise HTTPException(status_code=409, detail='Route already accepted')
            row.accepted_by_tg_id = current_user.tg_id
            row.status = 'accepted'
            await _grant_chat_access(session, trip_type='intercity_route', trip_id=row.id, user_ids=[row.creator_tg_id, current_user.tg_id], granted_by_tg_id=current_user.tg_id)
            await session.commit()
            return IntercityAcceptResponse(trip_id=row.id, trip_type='intercity_route', status=row.status)
        if kind == 'request':
            row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == item_id).with_for_update())
            if not await _eligible_request(row, current_user):
                raise HTTPException(status_code=403, detail='Request is not available for acceptance')
            if row.accepted_by_tg_id and row.accepted_by_tg_id != current_user.tg_id:
                raise HTTPException(status_code=409, detail='Request already accepted')
            row.accepted_by_tg_id = current_user.tg_id
            row.status = 'accepted'
            await _grant_chat_access(session, trip_type='intercity_request', trip_id=row.id, user_ids=[row.creator_tg_id, current_user.tg_id], granted_by_tg_id=current_user.tg_id)
            await session.commit()
            return IntercityAcceptResponse(trip_id=row.id, trip_type='intercity_request', status=row.status)
    raise HTTPException(status_code=400, detail='Unsupported intercity kind')


def install_intaxi_intercity_patch() -> None:
    if getattr(FastAPI, '_intaxi_intercity_patch_installed', False):
        return
    previous_add_api_route = FastAPI.add_api_route

    def patched_add_api_route(self, path: str, endpoint: Callable, *args: Any, **kwargs: Any):
        methods = {str(m).upper() for m in (kwargs.get('methods') or [])}
        replacement = endpoint
        if path == '/intercity/offers' and 'GET' in methods:
            replacement = safe_intercity_offers
        elif path == '/intercity/offers/{kind}/{item_id}' and 'GET' in methods:
            replacement = safe_intercity_offer_detail
        elif path == '/intercity/offers/{kind}/{item_id}/accept' and 'POST' in methods:
            replacement = safe_intercity_accept
        return previous_add_api_route(self, path, replacement, *args, **kwargs)

    FastAPI.add_api_route = patched_add_api_route
    setattr(FastAPI, '_intaxi_intercity_patch_installed', True)
