from __future__ import annotations

from math import ceil

from aiogram import Bot
from fastapi import HTTPException
from sqlalchemy import or_, select

from api.config import get_bot_token
from api.schemas import (
    CityAcceptResponse,
    CityOrderCreateRequest,
    CityOrderCreateResponse,
    CityOrderListResponse,
    CityOrderResponse,
    CityTripResponse,
    CurrentTripResponse,
    RaisePriceRequest,
    TariffItem,
    TariffListResponse,
)
from api.services.pricing import DEFAULT_TARIFFS, haversine_km
from intaxi_bot.app.database.models import (
    CityOrderRuntime,
    CityOrderV1,
    CityTripV1,
    DriverOnlineState,
    IntercityRequestV1,
    IntercityRouteMeta,
    IntercityRouteV1,
    TariffSetting,
    User,
    Vehicle,
    async_session,
    utcnow,
)


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.replace(microsecond=0).isoformat() if hasattr(value, 'replace') else str(value)


def _vehicle_to_schema(vehicle: Vehicle | None):
    if not vehicle:
        return None
    from api.schemas import VehicleInfo
    return VehicleInfo(
        brand=vehicle.brand,
        model=vehicle.model,
        plate=vehicle.plate,
        color=vehicle.color,
        year=vehicle.year,
        photo_out=vehicle.photo_out,
        photo_in=vehicle.photo_in,
        photo_tech=vehicle.photo_tech,
        photo_license=vehicle.photo_license,
        approved=vehicle.approved,
        capacity=vehicle.capacity,
    )


async def _get_tariff(country: str | None) -> TariffSetting:
    country_code = (country or '').lower() or 'default'
    async with async_session() as session:
        row = await session.scalar(select(TariffSetting).where(TariffSetting.country == country_code))
        if row:
            return row
        currency, price_per_km = DEFAULT_TARIFFS.get(country_code, ('USD', 1.0))
        row = TariffSetting(country=country_code, currency=currency, price_per_km=price_per_km)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row


async def _currency_hint(country: str | None) -> tuple[str, str]:
    tariff = await _get_tariff(country)
    return tariff.currency, f'~{tariff.price_per_km:g} {tariff.currency}/km'


async def _recommended_price(country: str | None, from_lat: float | None, from_lng: float | None, to_lat: float | None, to_lng: float | None):
    currency, hint = await _currency_hint(country)
    if None in (from_lat, from_lng, to_lat, to_lng):
        return None, None, None, currency, hint
    distance = haversine_km(float(from_lat), float(from_lng), float(to_lat), float(to_lng))
    tariff = await _get_tariff(country)
    price = round(distance * float(tariff.price_per_km), 2)
    eta = max(3, ceil(distance / 0.45))
    return price, round(distance, 2), eta, tariff.currency, hint


async def _ensure_online_state(session, driver: User) -> DriverOnlineState:
    row = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == driver.tg_id))
    if not row:
        row = DriverOnlineState(driver_tg_id=driver.tg_id, is_online=False, country=driver.country, city=driver.city)
        session.add(row)
        await session.flush()
    return row


async def _dispatch_stage_and_seen(session, country: str | None, city: str | None, from_lat: float | None, from_lng: float | None):
    if from_lat is None or from_lng is None:
        return 'manual_only', 0, None, None
    users = (await session.scalars(select(User).where(User.is_verified == True))).all()
    online_rows = (await session.scalars(select(DriverOnlineState).where(DriverOnlineState.is_online == True))).all()
    online_by_id = {row.driver_tg_id: row for row in online_rows if row.lat is not None and row.lng is not None}
    candidates = []
    for user in users:
        if user.tg_id in online_by_id and (not country or user.country == country):
            row = online_by_id[user.tg_id]
            dist = haversine_km(float(from_lat), float(from_lng), float(row.lat), float(row.lng))
            candidates.append((dist, row))
    candidates.sort(key=lambda item: item[0])
    stage = 'all_online'
    thresholds = [3, 6, 12, 15]
    count = len(candidates)
    nearest = round(candidates[0][0], 2) if candidates else None
    eta = max(2, ceil(nearest / 0.45)) if nearest is not None else None
    for threshold in thresholds:
        if any(dist <= threshold for dist, _ in candidates):
            stage = f'{threshold}km'
            count = sum(1 for dist, _ in candidates if dist <= threshold)
            break
    return stage, count, nearest, eta


def _map_provider(country: str | None) -> str:
    return 'yandex' if country in {'uz', 'tr'} else 'google'


def _map_urls(country: str | None, lat: float | None, lng: float | None, to_lat: float | None = None, to_lng: float | None = None):
    provider = _map_provider(country)
    if lat is None or lng is None:
        return provider, None, None
    if provider == 'yandex':
        return provider, f'https://yandex.com/map-widget/v1/?ll={lng}%2C{lat}&z=12&pt={lng},{lat},pm2rdm', f'https://yandex.com/maps/?ll={lng},{lat}&z=12&pt={lng},{lat},pm2rdm'
    query = f'{lat},{lng}'
    action = f'https://www.google.com/maps/dir/?api=1&origin={lat},{lng}&destination={to_lat},{to_lng}' if to_lat is not None and to_lng is not None else f'https://www.google.com/maps?q={query}'
    return provider, f'https://maps.google.com/maps?q={query}&z=12&output=embed', action


async def list_tariffs() -> TariffListResponse:
    async with async_session() as session:
        rows = (await session.scalars(select(TariffSetting).order_by(TariffSetting.country))).all()
        return TariffListResponse(items=[TariffItem(country=row.country, currency=row.currency, price_per_km=row.price_per_km) for row in rows])


async def city_order_to_schema(order: CityOrderV1, current_user: User | None = None) -> CityOrderResponse:
    async with async_session() as session:
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
        creator = await session.scalar(select(User).where(User.tg_id == order.creator_tg_id))
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == creator.id)) if order.role == 'driver' and creator else None
        driver_distance = driver_eta = None
        if runtime and runtime.active_trip_id:
            trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == runtime.active_trip_id))
            if trip and runtime.from_lat is not None and runtime.from_lng is not None and trip.driver_lat is not None and trip.driver_lng is not None:
                driver_distance = round(haversine_km(runtime.from_lat, runtime.from_lng, trip.driver_lat, trip.driver_lng), 2)
                driver_eta = max(2, ceil(driver_distance / 0.45))
        return CityOrderResponse(id=order.id, creator_tg_id=order.creator_tg_id, creator_name=creator.full_name if creator else None, creator_rating=float(creator.rating) if creator else None, role=order.role, country=order.country, city=order.city, from_address=order.from_address, to_address=order.to_address, seats=order.seats, price=float(order.price or 0), recommended_price=float(runtime.recommended_price) if runtime and runtime.recommended_price is not None else None, seen_by_drivers=int(runtime.seen_by_drivers) if runtime else None, can_raise_price_after=30, estimated_distance_km=float(runtime.estimated_distance_km) if runtime and runtime.estimated_distance_km is not None else None, estimated_trip_min=int(runtime.estimated_trip_min) if runtime and runtime.estimated_trip_min is not None else None, driver_distance_km=driver_distance, driver_eta_min=driver_eta, comment=order.comment, status=order.status, created_at=_iso(order.created_at), is_mine=bool(current_user and current_user.tg_id == order.creator_tg_id), active_trip_id=int(runtime.active_trip_id) if runtime and runtime.active_trip_id is not None else None, vehicle=_vehicle_to_schema(vehicle), currency=runtime.currency if runtime else None, tariff_hint=runtime.tariff_hint if runtime else None)


async def city_trip_to_schema(trip: CityTripV1) -> CityTripResponse:
    from api.schemas import CityTripResponse
    async with async_session() as session:
        passenger = await session.scalar(select(User).where(User.tg_id == trip.passenger_tg_id))
        driver = await session.scalar(select(User).where(User.tg_id == trip.driver_tg_id))
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == driver.id)) if driver else None
    provider, embed, action = _map_urls(trip.country, trip.pickup_lat, trip.pickup_lng, trip.destination_lat, trip.destination_lng)
    eta = max(2, ceil(haversine_km(trip.driver_lat, trip.driver_lng, trip.pickup_lat, trip.pickup_lng) / 0.45)) if trip.driver_lat is not None and trip.driver_lng is not None and trip.pickup_lat is not None and trip.pickup_lng is not None else None
    return CityTripResponse(id=trip.id, order_id=trip.order_id, status=trip.status, price=float(trip.price or 0), country=trip.country, city=trip.city, from_address=trip.from_address, to_address=trip.to_address, seats=trip.seats, comment=trip.comment, passenger_tg_id=trip.passenger_tg_id, driver_tg_id=trip.driver_tg_id, passenger_name=passenger.full_name if passenger else None, passenger_username=passenger.username if passenger else None, driver_name=driver.full_name if driver else None, driver_username=driver.username if driver else None, driver_rating=float(driver.rating) if driver else None, vehicle=_vehicle_to_schema(vehicle), trip_type='city_trip', pickup_lat=trip.pickup_lat, pickup_lng=trip.pickup_lng, destination_lat=trip.destination_lat, destination_lng=trip.destination_lng, driver_lat=trip.driver_lat, driver_lng=trip.driver_lng, passenger_lat=trip.passenger_lat, passenger_lng=trip.passenger_lng, map_provider=provider, map_embed_url=embed, map_action_url=action, eta_min=eta)

# other service methods omitted for brevity in command


async def create_city_order(payload: CityOrderCreateRequest, current_user: User) -> CityOrderCreateResponse:
    if payload.role not in {'driver', 'passenger'}:
        raise HTTPException(status_code=400, detail='role must be driver or passenger')
    if payload.role == 'driver' and not current_user.is_verified:
        raise HTTPException(status_code=403, detail='Only verified drivers can create driver offers')
    system_price, dist_km, eta, currency, hint = await _recommended_price(payload.country, payload.from_lat, payload.from_lng, payload.to_lat, payload.to_lng)
    final_price = float(payload.price) if payload.price is not None and payload.price > 0 else (system_price if system_price is not None else None)
    if final_price is None: raise HTTPException(status_code=400, detail='Own price is required when coordinates are missing')
    async with async_session() as session:
        order=CityOrderV1(creator_tg_id=current_user.tg_id, role=payload.role, country=payload.country, city=payload.city, from_address=payload.from_address, to_address=payload.to_address, seats=max(1,int(payload.seats or 1)), price=float(final_price), comment=payload.comment, status='active')
        session.add(order); await session.flush()
        stage, seen, _, _ = await _dispatch_stage_and_seen(session, payload.country, payload.city, payload.from_lat, payload.from_lng)
        session.add(CityOrderRuntime(order_id=order.id,currency=currency,tariff_hint=hint,recommended_price=system_price,system_price=system_price,from_lat=payload.from_lat,from_lng=payload.from_lng,to_lat=payload.to_lat,to_lng=payload.to_lng,estimated_distance_km=dist_km,estimated_trip_min=eta,dispatch_stage=stage,seen_by_drivers=seen))
        await session.commit()
        return CityOrderCreateResponse(id=order.id,status=order.status,recommended_price=system_price,seen_by_drivers=seen,currency=currency,tariff_hint=hint)

async def city_offers(kind:str,current_user:User)->CityOrderListResponse:
    async with async_session() as session: rows=(await session.scalars(select(CityOrderV1).order_by(CityOrderV1.id.desc()))).all()
    items=[]
    for row in rows:
        if row.status not in {'active','accepted','in_progress'}: continue
        if kind=='driver' and row.role!='driver': continue
        if kind=='passenger' and row.role!='passenger': continue
        if row.role=='passenger' and current_user.active_role!='driver' and current_user.tg_id!=row.creator_tg_id: continue
        items.append(await city_order_to_schema(row,current_user))
    return CityOrderListResponse(items=items)

async def get_city_offer_detail(order_id:int,current_user:User)->CityOrderResponse:
    async with async_session() as session: row=await session.scalar(select(CityOrderV1).where(CityOrderV1.id==order_id))
    if not row: raise HTTPException(status_code=404,detail='Order not found')
    if row.role=='passenger' and current_user.active_role!='driver' and current_user.tg_id!=row.creator_tg_id: raise HTTPException(status_code=403, detail='Forbidden')
    return await city_order_to_schema(row,current_user)

async def city_my_orders(current_user:User)->CityOrderListResponse:
    async with async_session() as session: rows=(await session.scalars(select(CityOrderV1).where(CityOrderV1.creator_tg_id==current_user.tg_id).order_by(CityOrderV1.id.desc()))).all()
    return CityOrderListResponse(items=[await city_order_to_schema(r,current_user) for r in rows])

async def city_close(order_id:int,current_user:User)->dict:
    async with async_session() as session:
        row=await session.scalar(select(CityOrderV1).where(CityOrderV1.id==order_id,CityOrderV1.creator_tg_id==current_user.tg_id))
        if not row: raise HTTPException(status_code=404, detail='Order not found')
        row.status='closed'; await session.commit(); return {'id':row.id,'status':row.status}

async def city_raise_price(order_id:int,payload:RaisePriceRequest,current_user:User)->dict:
    async with async_session() as session:
        row=await session.scalar(select(CityOrderV1).where(CityOrderV1.id==order_id,CityOrderV1.creator_tg_id==current_user.tg_id))
        if not row: raise HTTPException(status_code=404, detail='Order not found')
        row.price=float(payload.price); await session.commit(); return {'id':row.id,'status':row.status,'price':row.price}

async def city_accept(order_id:int,current_user:User)->CityAcceptResponse:
    async with async_session() as session:
        order=await session.scalar(select(CityOrderV1).where(CityOrderV1.id==order_id))
        if not order: raise HTTPException(status_code=404, detail='Order not found')
        if current_user.tg_id==order.creator_tg_id: raise HTTPException(status_code=403, detail='You cannot accept your own order')
        trip=CityTripV1(order_id=order.id,status='accepted',price=float(order.price or 0),country=order.country,city=order.city,from_address=order.from_address,to_address=order.to_address,seats=order.seats,comment=order.comment,passenger_tg_id=(order.creator_tg_id if order.role=='passenger' else current_user.tg_id),driver_tg_id=(current_user.tg_id if order.role=='passenger' else order.creator_tg_id))
        session.add(trip); order.status='accepted'; await session.flush(); await session.commit(); return CityAcceptResponse(trip_id=trip.id,status='accepted')

async def city_trip_detail(trip_id:int,current_user:User)->CityTripResponse:
    async with async_session() as session: trip=await session.scalar(select(CityTripV1).where(CityTripV1.id==trip_id))
    if not trip: raise HTTPException(status_code=404, detail='Trip not found')
    if current_user.tg_id not in {trip.passenger_tg_id, trip.driver_tg_id}: raise HTTPException(status_code=403,detail='Forbidden')
    return await city_trip_to_schema(trip)

async def city_trip_status(trip_id:int,payload,current_user:User)->CityTripResponse:
    allowed={'accepted','driver_on_way','driver_arrived','in_progress','completed','cancelled'}
    if payload.status not in allowed: raise HTTPException(status_code=400,detail='Unsupported status')
    async with async_session() as session:
        trip=await session.scalar(select(CityTripV1).where(CityTripV1.id==trip_id))
        if not trip: raise HTTPException(status_code=404, detail='Trip not found')
        if current_user.tg_id not in {trip.passenger_tg_id, trip.driver_tg_id}: raise HTTPException(status_code=403,detail='Forbidden')
        trip.status=payload.status; trip.updated_at=utcnow(); await session.commit(); await session.refresh(trip)
    return await city_trip_to_schema(trip)

async def current_trip(current_user:User)->CurrentTripResponse:
    async with async_session() as session:
        trip=await session.scalar(select(CityTripV1).where(or_(CityTripV1.passenger_tg_id==current_user.tg_id,CityTripV1.driver_tg_id==current_user.tg_id),CityTripV1.status.in_(['accepted','driver_on_way','driver_arrived','in_progress'])).order_by(CityTripV1.id.desc()))
        if trip: return CurrentTripResponse(item=(await city_trip_to_schema(trip)).model_dump())
    return CurrentTripResponse(item=None)
