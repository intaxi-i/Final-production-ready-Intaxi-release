from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select

from api.auth import get_current_user
from api.schemas import (
    CityAcceptResponse,
    CityOrderCreateRequest,
    CityOrderCreateResponse,
    CityOrderEnvelope,
    CityOrderListResponse,
    CityOrderResponse,
    CityTripEnvelope,
    CityTripStatusUpdateRequest,
    CurrentTripResponse,
    RaisePriceRequest,
    TariffItem,
    TariffListResponse,
)
from intaxi_bot.app.database.models import (
    CityOrderRuntime,
    CityOrderV1,
    CityTripV1,
    IntercityRequestV1,
    IntercityRouteMeta,
    IntercityRouteV1,
    TariffSetting,
    User,
    Vehicle,
    async_session,
    utcnow,
)

router = APIRouter()


@router.get('/city/tariffs', response_model=TariffListResponse)
async def city_tariffs(current_user: User = Depends(get_current_user)) -> TariffListResponse:
    async with async_session() as session:
        rows = (await session.scalars(select(TariffSetting).order_by(TariffSetting.country))).all()
        return TariffListResponse(items=[TariffItem(country=row.country, currency=row.currency, price_per_km=row.price_per_km) for row in rows])


@router.post('/city/orders', response_model=CityOrderCreateResponse)
async def create_city_order(payload: CityOrderCreateRequest, current_user: User = Depends(get_current_user)) -> CityOrderCreateResponse:
    from api import main as main_mod

    if payload.role not in {'driver', 'passenger'}:
        raise HTTPException(status_code=400, detail='role must be driver or passenger')
    if payload.role == 'driver':
        await main_mod._require_verified_driver(current_user, detail='Only verified drivers can create driver offers')
    system_price, dist_km, eta, currency, hint = await main_mod._recommended_price(payload.country, payload.from_lat, payload.from_lng, payload.to_lat, payload.to_lng)
    final_price = float(payload.price) if payload.price is not None and payload.price > 0 else (system_price if system_price is not None else None)
    if final_price is None:
        raise HTTPException(status_code=400, detail='Own price is required when coordinates are missing')
    async with async_session() as session:
        order = CityOrderV1(
            creator_tg_id=current_user.tg_id,
            role=payload.role,
            country=payload.country,
            city=payload.city,
            from_address=payload.from_address,
            to_address=payload.to_address,
            seats=max(1, int(payload.seats or 1)),
            price=float(final_price),
            comment=payload.comment,
            status='active',
        )
        session.add(order)
        await session.flush()
        stage, seen, _nearest, _driver_eta = await main_mod._dispatch_stage_and_seen(session, payload.country, payload.city, payload.from_lat, payload.from_lng)
        runtime = CityOrderRuntime(
            order_id=order.id,
            currency=currency,
            tariff_hint=hint,
            recommended_price=system_price,
            system_price=system_price,
            from_lat=payload.from_lat,
            from_lng=payload.from_lng,
            to_lat=payload.to_lat,
            to_lng=payload.to_lng,
            estimated_distance_km=dist_km,
            estimated_trip_min=eta,
            dispatch_stage=stage,
            seen_by_drivers=seen,
        )
        session.add(runtime)
        await session.commit()
        return CityOrderCreateResponse(id=order.id, status=order.status, recommended_price=system_price, seen_by_drivers=seen, currency=currency, tariff_hint=hint)


@router.get('/city/offers', response_model=CityOrderListResponse)
async def city_offers(kind: str = Query('all'), current_user: User = Depends(get_current_user)) -> CityOrderListResponse:
    from api import main as main_mod

    async with async_session() as session:
        rows = (await session.scalars(select(CityOrderV1).order_by(CityOrderV1.id.desc()))).all()
    items: list[CityOrderResponse] = []
    for row in rows:
        if row.status not in {'active', 'accepted', 'in_progress'}:
            continue
        if kind == 'driver' and row.role != 'driver':
            continue
        if kind == 'passenger' and row.role != 'passenger':
            continue
        if row.role == 'passenger' and current_user.active_role != 'driver' and current_user.tg_id != row.creator_tg_id:
            continue
        items.append(await main_mod._city_order_to_schema(row, current_user=current_user))
    return CityOrderListResponse(items=items)


@router.get('/city/offers/{order_id}', response_model=CityOrderEnvelope)
async def city_offer_detail(order_id: int, current_user: User = Depends(get_current_user)) -> CityOrderEnvelope:
    from api import main as main_mod

    async with async_session() as session:
        row = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id))
    if not row:
        raise HTTPException(status_code=404, detail='Order not found')
    if row.role == 'passenger' and current_user.active_role != 'driver' and current_user.tg_id != row.creator_tg_id:
        raise HTTPException(status_code=403, detail='Forbidden')
    if row.role == 'driver' and current_user.active_role == 'passenger' and current_user.tg_id != row.creator_tg_id:
        pass
    return CityOrderEnvelope(item=await main_mod._city_order_to_schema(row, current_user=current_user))


@router.get('/city/my-orders', response_model=CityOrderListResponse)
async def city_my_orders(current_user: User = Depends(get_current_user)) -> CityOrderListResponse:
    from api import main as main_mod

    async with async_session() as session:
        rows = (await session.scalars(select(CityOrderV1).where(CityOrderV1.creator_tg_id == current_user.tg_id).order_by(CityOrderV1.id.desc()))).all()
    return CityOrderListResponse(items=[await main_mod._city_order_to_schema(row, current_user=current_user) for row in rows])


@router.post('/city/orders/{order_id}/close')
async def city_close(order_id: int, current_user: User = Depends(get_current_user)) -> dict:
    async with async_session() as session:
        row = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id, CityOrderV1.creator_tg_id == current_user.tg_id))
        if not row:
            raise HTTPException(status_code=404, detail='Order not found')
        row.status = 'closed'
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == row.id))
        if runtime and runtime.active_trip_id:
            trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == runtime.active_trip_id))
            if trip and trip.status not in {'completed', 'cancelled'}:
                trip.status = 'cancelled'
                trip.cancelled_at = utcnow()
                trip.updated_at = utcnow()
        await session.commit()
        return {'id': row.id, 'status': row.status}


@router.post('/city/orders/{order_id}/raise-price')
async def city_raise_price(order_id: int, payload: RaisePriceRequest, current_user: User = Depends(get_current_user)) -> dict:
    async with async_session() as session:
        row = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id, CityOrderV1.creator_tg_id == current_user.tg_id))
        if not row:
            raise HTTPException(status_code=404, detail='Order not found')
        row.price = float(payload.price)
        await session.commit()
        return {'id': row.id, 'status': row.status, 'price': row.price}


@router.post('/city/offers/{order_id}/accept', response_model=CityAcceptResponse)
async def city_accept(order_id: int, current_user: User = Depends(get_current_user)) -> CityAcceptResponse:
    from api import main as main_mod

    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id))
        if not order:
            raise HTTPException(status_code=404, detail='Order not found')
        if current_user.tg_id == order.creator_tg_id:
            raise HTTPException(status_code=403, detail='You cannot accept your own order')
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
        if runtime and runtime.active_trip_id:
            trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == runtime.active_trip_id))
            if trip and current_user.tg_id in {trip.passenger_tg_id, trip.driver_tg_id}:
                return CityAcceptResponse(trip_id=runtime.active_trip_id, status=trip.status or 'accepted')
            raise HTTPException(status_code=409, detail='Order has already been accepted')

        if order.role == 'passenger':
            driver_user = await session.scalar(select(User).where(User.tg_id == current_user.tg_id))
            if not driver_user or not driver_user.is_verified:
                raise HTTPException(status_code=403, detail='Only verified drivers can accept passenger orders')
            passenger_tg_id = order.creator_tg_id
            driver_tg_id = current_user.tg_id
            online = await main_mod._ensure_online_state(session, current_user)
            online.is_online = True
            online.country = current_user.country
            online.city = current_user.city
            online.updated_at = utcnow()
            vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == driver_user.id))
        else:
            if current_user.active_role == 'driver':
                raise HTTPException(status_code=403, detail='Passenger should accept driver offers')
            passenger_tg_id = current_user.tg_id
            driver_tg_id = order.creator_tg_id
            driver_user = await session.scalar(select(User).where(User.tg_id == driver_tg_id))
            if not driver_user or not driver_user.is_verified:
                raise HTTPException(status_code=409, detail='Driver offer is not available for acceptance')
            vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == driver_user.id))
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
            pickup_lat=runtime.from_lat if runtime else None,
            pickup_lng=runtime.from_lng if runtime else None,
            destination_lat=runtime.to_lat if runtime else None,
            destination_lng=runtime.to_lng if runtime else None,
        )
        session.add(trip)
        await session.flush()
        if runtime:
            runtime.active_trip_id = trip.id
        order.status = 'accepted'
        await session.commit()
        await main_mod._send_driver_card_to_passenger(passenger_tg_id, driver_user, vehicle)
        return CityAcceptResponse(trip_id=trip.id, status='accepted')


@router.get('/city/trips/{trip_id}', response_model=CityTripEnvelope)
async def city_trip_detail(trip_id: int, current_user: User = Depends(get_current_user)) -> CityTripEnvelope:
    from api import main as main_mod

    async with async_session() as session:
        trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == trip_id))
    if not trip:
        raise HTTPException(status_code=404, detail='Trip not found')
    if current_user.tg_id not in {trip.passenger_tg_id, trip.driver_tg_id}:
        raise HTTPException(status_code=403, detail='Forbidden')
    return CityTripEnvelope(item=await main_mod._city_trip_to_schema(trip))


@router.post('/city/trips/{trip_id}/status', response_model=CityTripEnvelope)
async def city_trip_status(trip_id: int, payload: CityTripStatusUpdateRequest, current_user: User = Depends(get_current_user)) -> CityTripEnvelope:
    from api import main as main_mod

    allowed = {'accepted', 'driver_on_way', 'driver_arrived', 'in_progress', 'completed', 'cancelled'}
    if payload.status not in allowed:
        raise HTTPException(status_code=400, detail='Unsupported status')
    async with async_session() as session:
        trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == trip_id))
        if not trip:
            raise HTTPException(status_code=404, detail='Trip not found')
        if current_user.tg_id not in {trip.passenger_tg_id, trip.driver_tg_id}:
            raise HTTPException(status_code=403, detail='Forbidden')
        trip.status = payload.status
        trip.updated_at = utcnow()
        if payload.status == 'cancelled':
            trip.cancelled_at = utcnow()
        if payload.status == 'completed':
            trip.completed_at = utcnow()
            driver = await session.scalar(select(User).where(User.tg_id == trip.driver_tg_id))
            if driver:
                driver.commission_due = 0.0
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == trip.order_id))
        if order:
            if payload.status == 'completed':
                order.status = 'completed'
            elif payload.status == 'cancelled':
                order.status = 'cancelled'
        await session.commit()
        await session.refresh(trip)
        return CityTripEnvelope(item=await main_mod._city_trip_to_schema(trip))


@router.get('/trip/current', response_model=CurrentTripResponse)
async def current_trip(current_user: User = Depends(get_current_user)) -> CurrentTripResponse:
    from api import main as main_mod

    async with async_session() as session:
        trip = await session.scalar(select(CityTripV1).where(or_(CityTripV1.passenger_tg_id == current_user.tg_id, CityTripV1.driver_tg_id == current_user.tg_id), CityTripV1.status.in_(['accepted', 'driver_on_way', 'driver_arrived', 'in_progress'])).order_by(CityTripV1.id.desc()))
        if trip:
            item = (await main_mod._city_trip_to_schema(trip)).model_dump()
            return CurrentTripResponse(item=item)
        route = await session.scalar(select(IntercityRouteV1).where(or_(IntercityRouteV1.creator_tg_id == current_user.tg_id, IntercityRouteV1.accepted_by_tg_id == current_user.tg_id), IntercityRouteV1.status.in_(['active', 'accepted', 'in_progress'])).order_by(IntercityRouteV1.id.desc()))
        if route:
            meta = await session.scalar(select(IntercityRouteMeta).where(IntercityRouteMeta.route_id == route.id))
            provider, embed, action = main_mod._map_urls(route.country, meta.meeting_lat if meta else None, meta.meeting_lng if meta else None)
            return CurrentTripResponse(item={
                'id': route.id, 'trip_type': 'intercity_route', 'status': route.status, 'price': route.price,
                'from_city': route.from_city, 'to_city': route.to_city, 'comment': route.comment,
                'pickup_mode': meta.pickup_mode if meta else 'ask_driver', 'map_provider': provider, 'map_embed_url': embed, 'map_action_url': action,
                'date': route.departure_date, 'time': route.departure_time, 'accepted_by_tg_id': route.accepted_by_tg_id,
                'creator_tg_id': route.creator_tg_id, 'is_mine': current_user.tg_id == route.creator_tg_id,
            })
        req = await session.scalar(select(IntercityRequestV1).where(or_(IntercityRequestV1.creator_tg_id == current_user.tg_id, IntercityRequestV1.accepted_by_tg_id == current_user.tg_id), IntercityRequestV1.status.in_(['active', 'accepted', 'in_progress'])).order_by(IntercityRequestV1.id.desc()))
        if req:
            provider, embed, action = main_mod._map_urls(req.country, None, None)
            return CurrentTripResponse(item={
                'id': req.id, 'trip_type': 'intercity_request', 'status': req.status, 'price': req.price_offer,
                'from_city': req.from_city, 'to_city': req.to_city, 'comment': req.comment, 'map_provider': provider, 'map_embed_url': embed, 'map_action_url': action,
                'date': req.desired_date, 'time': req.desired_time, 'accepted_by_tg_id': req.accepted_by_tg_id,
                'creator_tg_id': req.creator_tg_id, 'is_mine': current_user.tg_id == req.creator_tg_id,
            })
    return CurrentTripResponse(item=None)
