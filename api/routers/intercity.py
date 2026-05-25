from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from api.auth import get_current_user
from api.schemas import (
    IntercityAcceptResponse,
    IntercityOfferEnvelope,
    IntercityOfferListResponse,
    IntercityOwnRequestListResponse,
    IntercityOwnRequestResponse,
    IntercityOwnRouteListResponse,
    IntercityRequestCreateRequest,
    IntercityRouteCreateRequest,
    IntercityStatusUpdateRequest,
)
from api.services import intercity as svc
from intaxi_bot.app.database.models import IntercityRequestV1, IntercityRouteMeta, IntercityRouteV1, User, async_session

router = APIRouter()


async def _require_verified_driver(current_user: User, *, detail: str = 'Only verified drivers can use this feature') -> None:
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail=detail)


@router.post('/intercity/chat-access/{kind}/{item_id}')
async def intercity_chat_access(kind: str, item_id: int, current_user: User = Depends(get_current_user)) -> dict:
    trip_type = f'intercity_{kind}'
    async with async_session() as session:
        await svc.grant_intercity_chat_access(session, trip_type=trip_type, trip_id=item_id, current_user=current_user)
        await session.commit()
    return {'status': 'granted', 'trip_type': trip_type, 'trip_id': item_id}


@router.post('/intercity/routes')
async def create_intercity_route(payload: IntercityRouteCreateRequest, current_user: User = Depends(get_current_user)) -> dict:
    await _require_verified_driver(current_user, detail='Only verified drivers can create intercity routes')
    async with async_session() as session:
        row = IntercityRouteV1(creator_tg_id=current_user.tg_id, country=payload.country, from_city=payload.from_city, to_city=payload.to_city, departure_date=payload.date, departure_time=payload.time, seats=payload.seats, price=payload.price, comment=payload.comment, status='active')
        session.add(row)
        await session.flush()
        session.add(IntercityRouteMeta(route_id=row.id, pickup_mode=payload.pickup_mode or 'ask_driver'))
        await session.commit()
        return {'id': row.id, 'status': row.status}


@router.post('/intercity/requests')
async def create_intercity_request(payload: IntercityRequestCreateRequest, current_user: User = Depends(get_current_user)) -> dict:
    async with async_session() as session:
        row = IntercityRequestV1(creator_tg_id=current_user.tg_id, country=payload.country, from_city=payload.from_city, to_city=payload.to_city, desired_date=payload.date, desired_time=payload.time, seats_needed=payload.seats_needed, price_offer=payload.price_offer, comment=payload.comment, status='active')
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return {'id': row.id, 'status': row.status}


@router.get('/intercity/offers', response_model=IntercityOfferListResponse)
async def intercity_offers(current_user: User = Depends(get_current_user)) -> IntercityOfferListResponse:
    async with async_session() as session:
        routes = (await session.scalars(select(IntercityRouteV1).order_by(IntercityRouteV1.id.desc()))).all()
        requests = (await session.scalars(select(IntercityRequestV1).order_by(IntercityRequestV1.id.desc()))).all()
        items = [await svc.offer_from_route(session, row, current_user) for row in routes]
        items.extend([await svc.offer_from_request(session, row, current_user) for row in requests])
    items.sort(key=lambda item: item.id, reverse=True)
    return IntercityOfferListResponse(items=items)


@router.get('/intercity/offers/{kind}/{item_id}', response_model=IntercityOfferEnvelope)
async def intercity_offer_detail(kind: str, item_id: int, current_user: User = Depends(get_current_user)) -> IntercityOfferEnvelope:
    async with async_session() as session:
        if kind == 'route':
            row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == item_id))
            if not row:
                raise HTTPException(status_code=404, detail='Route not found')
            return IntercityOfferEnvelope(item=await svc.offer_from_route(session, row, current_user))
        row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == item_id))
        if not row:
            raise HTTPException(status_code=404, detail='Request not found')
        return IntercityOfferEnvelope(item=await svc.offer_from_request(session, row, current_user))


@router.post('/intercity/offers/{kind}/{item_id}/accept', response_model=IntercityAcceptResponse)
async def intercity_accept(kind: str, item_id: int, current_user: User = Depends(get_current_user)) -> IntercityAcceptResponse:
    async with async_session() as session:
        if kind == 'route':
            row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == item_id))
            if not row:
                raise HTTPException(status_code=404, detail='Route not found')
            if current_user.tg_id == row.creator_tg_id:
                raise HTTPException(status_code=403, detail='Owner cannot accept own route')
            if row.accepted_by_tg_id and row.accepted_by_tg_id != current_user.tg_id:
                raise HTTPException(status_code=409, detail='Route already accepted')
            svc.validate_transition(row.status, 'accepted')
            row.accepted_by_tg_id = current_user.tg_id
            row.status = 'accepted'
            await svc.grant_intercity_chat_access(session, trip_type='intercity_route', trip_id=row.id, current_user=current_user)
            await session.commit()
            return IntercityAcceptResponse(trip_id=row.id, trip_type='intercity_route', status=row.status)
        if kind == 'request':
            await _require_verified_driver(current_user, detail='Only verified drivers can accept passenger intercity requests')
            row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == item_id))
            if not row:
                raise HTTPException(status_code=404, detail='Request not found')
            if current_user.tg_id == row.creator_tg_id:
                raise HTTPException(status_code=403, detail='Owner cannot accept own request')
            if row.accepted_by_tg_id and row.accepted_by_tg_id != current_user.tg_id:
                raise HTTPException(status_code=409, detail='Request already accepted')
            svc.validate_transition(row.status, 'accepted')
            row.accepted_by_tg_id = current_user.tg_id
            row.status = 'accepted'
            await svc.grant_intercity_chat_access(session, trip_type='intercity_request', trip_id=row.id, current_user=current_user)
            await session.commit()
            return IntercityAcceptResponse(trip_id=row.id, trip_type='intercity_request', status=row.status)
        raise HTTPException(status_code=400, detail='Unsupported intercity kind')


@router.get('/intercity/my-routes', response_model=IntercityOwnRouteListResponse)
async def intercity_my_routes(current_user: User = Depends(get_current_user)) -> IntercityOwnRouteListResponse:
    async with async_session() as session:
        rows = (await session.scalars(select(IntercityRouteV1).where(IntercityRouteV1.creator_tg_id == current_user.tg_id).order_by(IntercityRouteV1.id.desc()))).all()
        return IntercityOwnRouteListResponse(items=[await svc.own_route_item(session, row) for row in rows])


@router.get('/intercity/my-requests', response_model=IntercityOwnRequestListResponse)
async def intercity_my_requests(current_user: User = Depends(get_current_user)) -> IntercityOwnRequestListResponse:
    async with async_session() as session:
        rows = (await session.scalars(select(IntercityRequestV1).where(IntercityRequestV1.creator_tg_id == current_user.tg_id).order_by(IntercityRequestV1.id.desc()))).all()
        items = [IntercityOwnRequestResponse(id=row.id, country=row.country, from_city=row.from_city, to_city=row.to_city, date=row.desired_date, time=row.desired_time, seats_needed=row.seats_needed, price_offer=row.price_offer, comment=row.comment, status=row.status, created_at=svc.to_iso(row.created_at)) for row in rows]
        return IntercityOwnRequestListResponse(items=items)


@router.post('/intercity/routes/{route_id}/status')
async def intercity_route_status(route_id: int, payload: IntercityStatusUpdateRequest, current_user: User = Depends(get_current_user)) -> dict:
    svc.validate_intercity_status(payload.status)
    async with async_session() as session:
        row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == route_id))
        if not row:
            raise HTTPException(status_code=404, detail='Route not found')
        if current_user.tg_id not in {row.creator_tg_id, row.accepted_by_tg_id}:
            raise HTTPException(status_code=403, detail='Forbidden')
        svc.validate_transition(row.status, payload.status)
        row.status = payload.status
        await session.commit()
        return {'id': row.id, 'status': row.status}


@router.post('/intercity/requests/{request_id}/status')
async def intercity_request_status(request_id: int, payload: IntercityStatusUpdateRequest, current_user: User = Depends(get_current_user)) -> dict:
    svc.validate_intercity_status(payload.status)
    async with async_session() as session:
        row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == request_id))
        if not row:
            raise HTTPException(status_code=404, detail='Request not found')
        if current_user.tg_id not in {row.creator_tg_id, row.accepted_by_tg_id}:
            raise HTTPException(status_code=403, detail='Forbidden')
        svc.validate_transition(row.status, payload.status)
        row.status = payload.status
        await session.commit()
        return {'id': row.id, 'status': row.status}
