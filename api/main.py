from __future__ import annotations

from datetime import datetime, timezone
from math import ceil

from aiogram import Bot
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_, select

from api.auth import create_session, get_bot_token, get_current_user, validate_telegram_init_data
from api.config import get_settings
from api.routers import city as city_router
from api.routers import driver as driver_router
from api.routers import me as me_router
from api.schemas import (
    ChatCreatedResponse,
    ChatMessageListResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    CityAcceptResponse,
    CityOrderCreateRequest,
    CityOrderCreateResponse,
    CityOrderEnvelope,
    CityOrderListResponse,
    CityOrderResponse,
    CityTripEnvelope,
    CityTripResponse,
    CityTripStatusUpdateRequest,
    CurrentTripResponse,
    DevSessionRequest,
    HistoryResponse,
    IntercityAcceptResponse,
    IntercityOfferEnvelope,
    IntercityOfferListResponse,
    IntercityOfferResponse,
    IntercityOwnRequestListResponse,
    IntercityOwnRequestResponse,
    IntercityOwnRouteListResponse,
    IntercityOwnRouteResponse,
    IntercityRequestCreateRequest,
    IntercityRouteCreateRequest,
    IntercityStatusUpdateRequest,
    PaymentApproveRequest,
    PaymentItem,
    PaymentListResponse,
    PaymentRequestCreate,
    PaymentReviewResponse,
    RaisePriceRequest,
    SessionResponse,
    TariffItem,
    TariffListResponse,
    TariffUpdateRequest,
    TelegramAuthRequest,
    UpdateProfileRequest,
    UpdateRoleRequest,
    UpdateVehicleRequest,
    UserEnvelope,
    UserMe,
    VehicleInfo,
    WalletResponse,
)
from intaxi_bot.app.database.models import (
    AdminRole,
    ChatMessageV1,
    CityOrderRuntime,
    CityOrderV1,
    CityTripV1,
    DriverOnlineState,
    DriverPaymentRequest,
    IntercityChatAccess,
    IntercityRequestV1,
    IntercityRouteMeta,
    IntercityRouteV1,
    TariffSetting,
    User,
    Vehicle,
    async_main,
    async_session,
    utcnow,
)
from intaxi_bot.app.database.requests import (
    DEFAULT_TARIFFS,
    admin_has_permission,
    approve_driver_payment_request,
    create_driver_payment_request,
    ensure_bootstrap_superadmins,
    get_or_create_user,
    haversine_km,
    register_vehicle,
    reject_driver_payment_request,
    set_user_reg,
)

app = FastAPI(title=get_settings().app_name)
app.include_router(me_router.router)
app.include_router(driver_router.router)
app.include_router(city_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.intaxi.best",
        "https://intaxi.pages.dev",
        "https://intaxi.best",
        "https://www.intaxi.best",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event('startup')
async def on_startup() -> None:
    await async_main()
    await ensure_bootstrap_superadmins()


COMMISSION_RATE = 0.0

ADMIN_CARD_BY_COUNTRY = {
    'uz': '8600310416548592',
    'uzcard': '8600310416548592',
    'tr': '4195250052390109',
    'sa': '4195250052390109',
    'visa': '4195250052390109',
}


def _admin_card_number(card_country: str | None) -> str | None:
    key = (card_country or '').strip().lower()
    return ADMIN_CARD_BY_COUNTRY.get(key)


def _allow_dev_session() -> bool:
    settings = get_settings()
    env = (settings.app_env or '').strip().lower()
    return env in {'development', 'dev', 'local', 'test'}


async def _require_verified_driver(current_user: User, *, detail: str = 'Only verified drivers can use this feature') -> None:
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail=detail)


async def _ensure_chat_access(session, current_user: User, trip_type: str, trip_id: int) -> None:
    if trip_type == 'city_trip':
        trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == trip_id))
        if not trip:
            raise HTTPException(status_code=404, detail='Trip not found')
        if current_user.tg_id not in {trip.passenger_tg_id, trip.driver_tg_id}:
            raise HTTPException(status_code=403, detail='Forbidden')
        return

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
        raise HTTPException(status_code=403, detail='Chat is not available for this object')

    access = await session.scalar(
        select(IntercityChatAccess).where(
            IntercityChatAccess.trip_type == trip_type,
            IntercityChatAccess.trip_id == trip_id,
            IntercityChatAccess.user_tg_id == current_user.tg_id,
        )
    )
    if not access:
        raise HTTPException(status_code=403, detail='Chat access is not granted')


async def _grant_intercity_chat_access(session, *, trip_type: str, trip_id: int, current_user: User) -> None:
    if trip_type == 'intercity_route':
        row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == trip_id))
        if not row:
            raise HTTPException(status_code=404, detail='Route not found')
        if current_user.tg_id in {row.creator_tg_id, row.accepted_by_tg_id}:
            return
        meta = await session.scalar(select(IntercityRouteMeta).where(IntercityRouteMeta.route_id == row.id))
        if meta and (meta.pickup_mode or 'ask_driver') != 'ask_driver':
            raise HTTPException(status_code=403, detail='Chat is disabled for this route')
        granted_by = row.creator_tg_id
        allowed_statuses = {'active', 'accepted', 'in_progress'}
    elif trip_type == 'intercity_request':
        row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == trip_id))
        if not row:
            raise HTTPException(status_code=404, detail='Request not found')
        if current_user.tg_id in {row.creator_tg_id, row.accepted_by_tg_id}:
            return
        granted_by = row.creator_tg_id
        allowed_statuses = {'active', 'accepted', 'in_progress'}
    else:
        raise HTTPException(status_code=400, detail='Unsupported intercity object type')

    if row.status not in allowed_statuses:
        raise HTTPException(status_code=403, detail='Chat is not available for closed items')

    access = await session.scalar(
        select(IntercityChatAccess).where(
            IntercityChatAccess.trip_type == trip_type,
            IntercityChatAccess.trip_id == trip_id,
            IntercityChatAccess.user_tg_id == current_user.tg_id,
        )
    )
    if access:
        return

    session.add(
        IntercityChatAccess(
            trip_type=trip_type,
            trip_id=trip_id,
            user_tg_id=current_user.tg_id,
            granted_by_tg_id=granted_by,
        )
    )


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat()
    return str(value)


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


async def _to_me(user: User) -> UserMe:
    async with async_session() as session:
        db_user = await session.scalar(select(User).where(User.id == user.id))
        if not db_user:
            raise HTTPException(status_code=404, detail='User not found')
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == db_user.id))

    return UserMe(
        tg_id=db_user.tg_id,
        full_name=db_user.full_name,
        username=db_user.username,
        language=db_user.language,
        country=db_user.country,
        city=db_user.city,
        balance=float(db_user.balance or 0),
        commission_due=0.0,
        free_rides_left=0,
        active_role=db_user.active_role,
        is_verified=bool(db_user.is_verified),
        vehicle=_vehicle_to_schema(vehicle),
    )


async def _set_user_active_role(tg_id: int, active_role: str) -> User | None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return None
        user.active_role = active_role
        await session.commit()
        await session.refresh(user)
        return user


async def _get_tariff(country: str | None) -> TariffSetting:
    country_key = (country or 'uz').lower()
    async with async_session() as session:
        row = await session.scalar(select(TariffSetting).where(TariffSetting.country == country_key))
        if row:
            return row
        currency, price = DEFAULT_TARIFFS.get(country_key, ('USD', 1.0))
        row = TariffSetting(country=country_key, currency=currency, price_per_km=price)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row


async def _currency_hint(country: str | None) -> tuple[str, str]:
    tariff = await _get_tariff(country)
    if tariff.country == 'uz':
        return tariff.currency, f'~{tariff.price_per_km:g} {tariff.currency}/km'
    return tariff.currency, f'~{tariff.price_per_km:g} {tariff.currency}/km'


async def _recommended_price(country: str | None, from_lat: float | None, from_lng: float | None, to_lat: float | None, to_lng: float | None) -> tuple[float | None, float | None, int | None, str | None, str | None]:
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


async def _dispatch_stage_and_seen(session, country: str | None, city: str | None, from_lat: float | None, from_lng: float | None) -> tuple[str, int, float | None, int | None]:
    if from_lat is None or from_lng is None:
        return 'manual_only', 0, None, None
    users = (await session.scalars(select(User).where(User.is_verified == True))).all()
    online_rows = (await session.scalars(select(DriverOnlineState).where(DriverOnlineState.is_online == True))).all()
    online_by_id = {row.driver_tg_id: row for row in online_rows if row.lat is not None and row.lng is not None}
    candidates: list[tuple[float, DriverOnlineState]] = []
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


async def _send_driver_card_to_passenger(passenger_tg_id: int, driver: User, vehicle: Vehicle | None) -> None:
    token = get_bot_token()
    if not token:
        return
    bot = Bot(token=token)
    try:
        media_fields = []
        if vehicle:
            media_fields = [vehicle.photo_tech, vehicle.photo_license, vehicle.photo_out, vehicle.photo_in]
        media = [item for item in media_fields if item]
        if media:
            try:
                await bot.send_media_group(passenger_tg_id, [__import__('aiogram').types.InputMediaPhoto(media=m) for m in media])
            except Exception:
                pass
        title = 'Карточка водителя'
        text = (
            f'<b>{title}</b>\n\n'
            f'👤 {driver.full_name or "—"}\n'
            f'Username: @{driver.username or "—"}\n'
            f'⭐ {float(driver.rating or 0):.1f}\n'
        )
        if vehicle:
            text += (
                f'🚗 {vehicle.brand} {vehicle.model}\n'
                f'🔢 {vehicle.plate}\n'
            )
        await bot.send_message(passenger_tg_id, text, parse_mode='HTML')
    finally:
        await bot.session.close()


def _map_provider(country: str | None) -> str:
    if country in {'uz', 'tr'}:
        return 'yandex'
    return 'google'


def _map_urls(country: str | None, lat: float | None, lng: float | None, to_lat: float | None = None, to_lng: float | None = None):
    provider = _map_provider(country)
    if lat is None or lng is None:
        return provider, None, None
    if provider == 'yandex':
        embed = f'https://yandex.com/map-widget/v1/?ll={lng}%2C{lat}&z=12&pt={lng},{lat},pm2rdm'
        action = f'https://yandex.com/maps/?ll={lng},{lat}&z=12&pt={lng},{lat},pm2rdm'
    else:
        query = f'{lat},{lng}'
        if to_lat is not None and to_lng is not None:
            action = f'https://www.google.com/maps/dir/?api=1&origin={lat},{lng}&destination={to_lat},{to_lng}'
        else:
            action = f'https://www.google.com/maps?q={query}'
        embed = f'https://maps.google.com/maps?q={query}&z=12&output=embed'
    return provider, embed, action


async def _city_order_to_schema(order: CityOrderV1, current_user: User | None = None) -> CityOrderResponse:
    async with async_session() as session:
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
        creator = await session.scalar(select(User).where(User.tg_id == order.creator_tg_id))
        vehicle = None
        if order.role == 'driver' and creator:
            vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == creator.id))
        driver_distance = None
        driver_eta = None
        if runtime and runtime.active_trip_id:
            trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == runtime.active_trip_id))
            if trip and runtime.from_lat is not None and runtime.from_lng is not None and trip.driver_lat is not None and trip.driver_lng is not None:
                driver_distance = round(haversine_km(runtime.from_lat, runtime.from_lng, trip.driver_lat, trip.driver_lng), 2)
                driver_eta = max(2, ceil(driver_distance / 0.45))
        return CityOrderResponse(
            id=order.id,
            creator_tg_id=order.creator_tg_id,
            creator_name=creator.full_name if creator else None,
            creator_rating=float(creator.rating) if creator else None,
            role=order.role,
            country=order.country,
            city=order.city,
            from_address=order.from_address,
            to_address=order.to_address,
            seats=order.seats,
            price=float(order.price or 0),
            recommended_price=float(runtime.recommended_price) if runtime and runtime.recommended_price is not None else None,
            seen_by_drivers=int(runtime.seen_by_drivers) if runtime else None,
            can_raise_price_after=30,
            estimated_distance_km=float(runtime.estimated_distance_km) if runtime and runtime.estimated_distance_km is not None else None,
            estimated_trip_min=int(runtime.estimated_trip_min) if runtime and runtime.estimated_trip_min is not None else None,
            driver_distance_km=driver_distance,
            driver_eta_min=driver_eta,
            comment=order.comment,
            status=order.status,
            created_at=_iso(order.created_at),
            is_mine=bool(current_user and current_user.tg_id == order.creator_tg_id),
            active_trip_id=int(runtime.active_trip_id) if runtime and runtime.active_trip_id is not None else None,
            vehicle=_vehicle_to_schema(vehicle),
            currency=runtime.currency if runtime else None,
            tariff_hint=runtime.tariff_hint if runtime else None,
        )


async def _city_trip_to_schema(trip: CityTripV1) -> CityTripResponse:
    async with async_session() as session:
        passenger = await session.scalar(select(User).where(User.tg_id == trip.passenger_tg_id))
        driver = await session.scalar(select(User).where(User.tg_id == trip.driver_tg_id))
        vehicle = None
        if driver:
            vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == driver.id))
    provider, embed, action = _map_urls(trip.country, trip.pickup_lat, trip.pickup_lng, trip.destination_lat, trip.destination_lng)
    eta = None
    if trip.driver_lat is not None and trip.driver_lng is not None and trip.pickup_lat is not None and trip.pickup_lng is not None:
        eta = max(2, ceil(haversine_km(trip.driver_lat, trip.driver_lng, trip.pickup_lat, trip.pickup_lng) / 0.45))
    return CityTripResponse(
        id=trip.id,
        order_id=trip.order_id,
        status=trip.status,
        price=float(trip.price or 0),
        country=trip.country,
        city=trip.city,
        from_address=trip.from_address,
        to_address=trip.to_address,
        seats=trip.seats,
        comment=trip.comment,
        passenger_tg_id=trip.passenger_tg_id,
        driver_tg_id=trip.driver_tg_id,
        passenger_name=passenger.full_name if passenger else None,
        passenger_username=passenger.username if passenger else None,
        driver_name=driver.full_name if driver else None,
        driver_username=driver.username if driver else None,
        driver_rating=float(driver.rating) if driver else None,
        vehicle=_vehicle_to_schema(vehicle),
        trip_type='city_trip',
        pickup_lat=trip.pickup_lat,
        pickup_lng=trip.pickup_lng,
        destination_lat=trip.destination_lat,
        destination_lng=trip.destination_lng,
        driver_lat=trip.driver_lat,
        driver_lng=trip.driver_lng,
        passenger_lat=trip.passenger_lat,
        passenger_lng=trip.passenger_lng,
        map_provider=provider,
        map_embed_url=embed,
        map_action_url=action,
        eta_min=eta,
    )


async def _intercity_offer_from_route(route: IntercityRouteV1, current_user: User | None = None) -> IntercityOfferResponse:
    async with async_session() as session:
        creator = await session.scalar(select(User).where(User.tg_id == route.creator_tg_id))
        meta = await session.scalar(select(IntercityRouteMeta).where(IntercityRouteMeta.route_id == route.id))
    provider, embed, action = _map_urls(route.country, meta.meeting_lat if meta else None, meta.meeting_lng if meta else None)
    return IntercityOfferResponse(
        kind='route', id=route.id, creator_tg_id=route.creator_tg_id, creator_name=creator.full_name if creator else None,
        country=route.country, from_city=route.from_city, to_city=route.to_city, date=route.departure_date, time=route.departure_time,
        seats=route.seats, price=float(route.price or 0), comment=route.comment, status=route.status, created_at=_iso(route.created_at),
        is_mine=bool(current_user and current_user.tg_id == route.creator_tg_id), pickup_mode=meta.pickup_mode if meta else 'ask_driver',
        active_trip_id=route.id if route.status in {'accepted', 'in_progress'} else None,
        accepted_by_tg_id=route.accepted_by_tg_id,
        can_accept=bool(current_user and current_user.tg_id not in {route.creator_tg_id, route.accepted_by_tg_id} and route.status == 'active'),
        map_provider=provider, map_embed_url=embed, map_action_url=action,
    )


async def _intercity_offer_from_request(req: IntercityRequestV1, current_user: User | None = None) -> IntercityOfferResponse:
    async with async_session() as session:
        creator = await session.scalar(select(User).where(User.tg_id == req.creator_tg_id))
    provider, embed, action = _map_urls(req.country, None, None)
    return IntercityOfferResponse(
        kind='request', id=req.id, creator_tg_id=req.creator_tg_id, creator_name=creator.full_name if creator else None,
        country=req.country, from_city=req.from_city, to_city=req.to_city, date=req.desired_date, time=req.desired_time,
        seats=req.seats_needed, price=float(req.price_offer or 0), comment=req.comment, status=req.status, created_at=_iso(req.created_at),
        is_mine=bool(current_user and current_user.tg_id == req.creator_tg_id), pickup_mode='ask_driver',
        active_trip_id=req.id if req.status in {'accepted', 'in_progress'} else None,
        accepted_by_tg_id=req.accepted_by_tg_id,
        can_accept=bool(current_user and current_user.tg_id not in {req.creator_tg_id, req.accepted_by_tg_id} and req.status == 'active'),
        map_provider=provider, map_embed_url=embed, map_action_url=action,
    )


@app.post('/auth/telegram', response_model=SessionResponse)
async def auth_telegram(payload: TelegramAuthRequest) -> SessionResponse:
    tg_user = validate_telegram_init_data(payload.init_data, get_bot_token())
    user = await get_or_create_user(tg_user.tg_id, tg_user.full_name, tg_user.username)
    token = create_session(user.tg_id, user.full_name, user.username)
    me = await _to_me(user)
    return SessionResponse(session_token=token, user=me)


@app.post('/dev/session', response_model=SessionResponse)
async def dev_session(payload: DevSessionRequest | None = None) -> SessionResponse:
    if not _allow_dev_session():
        raise HTTPException(status_code=403, detail='dev/session is disabled in this environment')
    settings = get_settings()
    req = payload or DevSessionRequest()
    tg_id = req.tg_id or settings.dev_tg_id
    full_name = req.full_name or settings.dev_full_name
    username = req.username if req.username is not None else settings.dev_username
    user = await get_or_create_user(tg_id=tg_id, full_name=full_name, username=username)
    token = create_session(user.tg_id, user.full_name, user.username)
    me = await _to_me(user)
    return SessionResponse(session_token=token, user=me)




@app.get('/wallet', response_model=WalletResponse)
async def wallet(current_user: User = Depends(get_current_user)) -> WalletResponse:
    async with async_session() as session:
        db_user = await session.scalar(select(User).where(User.id == current_user.id))
        if not db_user:
            raise HTTPException(status_code=404, detail='User not found')
        return WalletResponse(
            balance=float(db_user.balance or 0),
            commission_due=0.0,
            free_rides_left=0,
            commission_rate=COMMISSION_RATE,
        )


@app.post('/wallet/topup', response_model=PaymentItem)
async def wallet_topup(payload: PaymentRequestCreate, current_user: User = Depends(get_current_user)) -> PaymentItem:
    row = await create_driver_payment_request(current_user.tg_id, payload.card_country, _admin_card_number(payload.card_country), payload.amount, payload.receipt_file_id)
    return PaymentItem(id=row.id, amount=row.amount, status=row.status, card_country=row.card_country, admin_card_number=row.admin_card_number, receipt_file_id=row.receipt_file_id, reviewed_by=row.reviewed_by, created_at=_iso(row.created_at), reviewed_at=_iso(row.reviewed_at), driver_tg_id=row.driver_tg_id, driver_balance=float(current_user.balance or 0))


@app.get('/wallet/topup/history', response_model=PaymentListResponse)
async def wallet_topup_history(current_user: User = Depends(get_current_user)) -> PaymentListResponse:
    async with async_session() as session:
        rows = (await session.scalars(select(DriverPaymentRequest).where(DriverPaymentRequest.driver_tg_id == current_user.tg_id).order_by(DriverPaymentRequest.id.desc()))).all()
        items = [PaymentItem(id=row.id, amount=row.amount, status=row.status, card_country=row.card_country, admin_card_number=row.admin_card_number, receipt_file_id=row.receipt_file_id, reviewed_by=row.reviewed_by, created_at=_iso(row.created_at), reviewed_at=_iso(row.reviewed_at), driver_tg_id=row.driver_tg_id, driver_balance=float(current_user.balance or 0)) for row in rows]
        return PaymentListResponse(items=items)


@app.get('/admin/payments/pending', response_model=PaymentListResponse)
async def admin_pending_payments(current_user: User = Depends(get_current_user)) -> PaymentListResponse:
    if not await admin_has_permission(current_user.tg_id, 'payments'):
        raise HTTPException(status_code=403, detail='Forbidden')
    async with async_session() as session:
        rows = (await session.scalars(select(DriverPaymentRequest).where(DriverPaymentRequest.status == 'pending').order_by(DriverPaymentRequest.id.desc()))).all()
        items = []
        for row in rows:
            driver = await session.scalar(select(User).where(User.tg_id == row.driver_tg_id))
            items.append(PaymentItem(id=row.id, amount=row.amount, status=row.status, card_country=row.card_country, admin_card_number=row.admin_card_number, receipt_file_id=row.receipt_file_id, reviewed_by=row.reviewed_by, created_at=_iso(row.created_at), reviewed_at=_iso(row.reviewed_at), driver_tg_id=row.driver_tg_id, driver_balance=float(driver.balance or 0) if driver else None))
        return PaymentListResponse(items=items)


@app.post('/admin/payments/{payment_id}/approve', response_model=PaymentReviewResponse)
async def admin_approve_payment(payment_id: int, payload: PaymentApproveRequest, current_user: User = Depends(get_current_user)) -> PaymentReviewResponse:
    if not await admin_has_permission(current_user.tg_id, 'payments'):
        raise HTTPException(status_code=403, detail='Forbidden')
    if payload.amount is not None:
        from intaxi_bot.app.database.requests import update_driver_payment_request_amount
        await update_driver_payment_request_amount(payment_id, payload.amount)
    result = await approve_driver_payment_request(payment_id, reviewed_by=current_user.tg_id)
    if not result:
        raise HTTPException(status_code=404, detail='Payment not found')
    req, user = result
    return PaymentReviewResponse(id=req.id, status=req.status, driver_tg_id=req.driver_tg_id, amount=req.amount, reviewed_by=req.reviewed_by, reviewed_at=_iso(req.reviewed_at), driver_balance=float(user.balance or 0))


@app.post('/admin/payments/{payment_id}/reject', response_model=PaymentReviewResponse)
async def admin_reject_payment(payment_id: int, current_user: User = Depends(get_current_user)) -> PaymentReviewResponse:
    if not await admin_has_permission(current_user.tg_id, 'payments'):
        raise HTTPException(status_code=403, detail='Forbidden')
    result = await reject_driver_payment_request(payment_id, reviewed_by=current_user.tg_id)
    if not result:
        raise HTTPException(status_code=404, detail='Payment not found')
    req, user = result
    return PaymentReviewResponse(id=req.id, status=req.status, driver_tg_id=req.driver_tg_id, amount=req.amount, reviewed_by=req.reviewed_by, reviewed_at=_iso(req.reviewed_at), driver_balance=float(user.balance or 0) if user else None)








@app.get('/chat/{trip_id}/messages', response_model=ChatMessageListResponse)
async def chat_messages(trip_id: int, trip_type: str = Query('generic'), current_user: User = Depends(get_current_user)) -> ChatMessageListResponse:
    async with async_session() as session:
        await _ensure_chat_access(session, current_user, trip_type, trip_id)
        rows = (await session.scalars(select(ChatMessageV1).where(ChatMessageV1.trip_id == trip_id, ChatMessageV1.trip_type == trip_type).order_by(ChatMessageV1.id.asc()))).all()
        return ChatMessageListResponse(items=[ChatMessageResponse(id=row.id, sender_tg_id=row.sender_tg_id, text=row.text, created_at=_iso(row.created_at) or '') for row in rows])


@app.post('/chat/{trip_id}/messages', response_model=ChatCreatedResponse)
async def chat_send(trip_id: int, payload: ChatMessageRequest, trip_type: str = Query('generic'), current_user: User = Depends(get_current_user)) -> ChatCreatedResponse:
    text_value = (payload.text or '').strip()
    if not text_value:
        raise HTTPException(status_code=400, detail='Message text is required')
    async with async_session() as session:
        await _ensure_chat_access(session, current_user, trip_type, trip_id)
        row = ChatMessageV1(trip_type=trip_type, trip_id=trip_id, sender_tg_id=current_user.tg_id, text=text_value)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return ChatCreatedResponse(id=row.id, status='sent')


@app.post('/intercity/chat-access/{kind}/{item_id}')
async def intercity_chat_access(kind: str, item_id: int, current_user: User = Depends(get_current_user)) -> dict:
    trip_type = f'intercity_{kind}'
    async with async_session() as session:
        await _grant_intercity_chat_access(session, trip_type=trip_type, trip_id=item_id, current_user=current_user)
        await session.commit()
    return {'status': 'granted', 'trip_type': trip_type, 'trip_id': item_id}


@app.post('/intercity/routes')
async def create_intercity_route(payload: IntercityRouteCreateRequest, current_user: User = Depends(get_current_user)) -> dict:
    await _require_verified_driver(current_user, detail='Only verified drivers can create intercity routes')
    async with async_session() as session:
        row = IntercityRouteV1(
            creator_tg_id=current_user.tg_id, country=payload.country, from_city=payload.from_city, to_city=payload.to_city,
            departure_date=payload.date, departure_time=payload.time, seats=payload.seats, price=payload.price, comment=payload.comment, status='active'
        )
        session.add(row)
        await session.flush()
        session.add(IntercityRouteMeta(route_id=row.id, pickup_mode=payload.pickup_mode or 'ask_driver'))
        await session.commit()
        return {'id': row.id, 'status': row.status}


@app.post('/intercity/requests')
async def create_intercity_request(payload: IntercityRequestCreateRequest, current_user: User = Depends(get_current_user)) -> dict:
    async with async_session() as session:
        row = IntercityRequestV1(
            creator_tg_id=current_user.tg_id, country=payload.country, from_city=payload.from_city, to_city=payload.to_city,
            desired_date=payload.date, desired_time=payload.time, seats_needed=payload.seats_needed, price_offer=payload.price_offer, comment=payload.comment, status='active'
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return {'id': row.id, 'status': row.status}


@app.get('/intercity/offers', response_model=IntercityOfferListResponse)
async def intercity_offers(current_user: User = Depends(get_current_user)) -> IntercityOfferListResponse:
    async with async_session() as session:
        routes = (await session.scalars(select(IntercityRouteV1).order_by(IntercityRouteV1.id.desc()))).all()
        requests = (await session.scalars(select(IntercityRequestV1).order_by(IntercityRequestV1.id.desc()))).all()
    items = [await _intercity_offer_from_route(row, current_user) for row in routes] + [await _intercity_offer_from_request(row, current_user) for row in requests]
    items.sort(key=lambda item: item.id, reverse=True)
    return IntercityOfferListResponse(items=items)


@app.get('/intercity/offers/{kind}/{item_id}', response_model=IntercityOfferEnvelope)
async def intercity_offer_detail(kind: str, item_id: int, current_user: User = Depends(get_current_user)) -> IntercityOfferEnvelope:
    async with async_session() as session:
        if kind == 'route':
            row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == item_id))
            if not row:
                raise HTTPException(status_code=404, detail='Route not found')
            return IntercityOfferEnvelope(item=await _intercity_offer_from_route(row, current_user))
        row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == item_id))
        if not row:
            raise HTTPException(status_code=404, detail='Request not found')
        return IntercityOfferEnvelope(item=await _intercity_offer_from_request(row, current_user))


@app.post('/intercity/offers/{kind}/{item_id}/accept', response_model=IntercityAcceptResponse)
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
            row.accepted_by_tg_id = current_user.tg_id
            row.status = 'accepted'
            await _grant_intercity_chat_access(session, trip_type='intercity_route', trip_id=row.id, current_user=current_user)
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
            row.accepted_by_tg_id = current_user.tg_id
            row.status = 'accepted'
            await _grant_intercity_chat_access(session, trip_type='intercity_request', trip_id=row.id, current_user=current_user)
            await session.commit()
            return IntercityAcceptResponse(trip_id=row.id, trip_type='intercity_request', status=row.status)
        raise HTTPException(status_code=400, detail='Unsupported intercity kind')


@app.get('/intercity/my-routes', response_model=IntercityOwnRouteListResponse)
async def intercity_my_routes(current_user: User = Depends(get_current_user)) -> IntercityOwnRouteListResponse:
    async with async_session() as session:
        rows = (await session.scalars(select(IntercityRouteV1).where(IntercityRouteV1.creator_tg_id == current_user.tg_id).order_by(IntercityRouteV1.id.desc()))).all()
        items = []
        for row in rows:
            meta = await session.scalar(select(IntercityRouteMeta).where(IntercityRouteMeta.route_id == row.id))
            items.append(IntercityOwnRouteResponse(id=row.id, country=row.country, from_city=row.from_city, to_city=row.to_city, date=row.departure_date, time=row.departure_time, seats=row.seats, price=row.price, comment=row.comment, status=row.status, created_at=_iso(row.created_at), pickup_mode=meta.pickup_mode if meta else 'ask_driver'))
        return IntercityOwnRouteListResponse(items=items)


@app.get('/intercity/my-requests', response_model=IntercityOwnRequestListResponse)
async def intercity_my_requests(current_user: User = Depends(get_current_user)) -> IntercityOwnRequestListResponse:
    async with async_session() as session:
        rows = (await session.scalars(select(IntercityRequestV1).where(IntercityRequestV1.creator_tg_id == current_user.tg_id).order_by(IntercityRequestV1.id.desc()))).all()
        items = [IntercityOwnRequestResponse(id=row.id, country=row.country, from_city=row.from_city, to_city=row.to_city, date=row.desired_date, time=row.desired_time, seats_needed=row.seats_needed, price_offer=row.price_offer, comment=row.comment, status=row.status, created_at=_iso(row.created_at)) for row in rows]
        return IntercityOwnRequestListResponse(items=items)



@app.post('/intercity/routes/{route_id}/status')
async def intercity_route_status(route_id: int, payload: IntercityStatusUpdateRequest, current_user: User = Depends(get_current_user)) -> dict:
    allowed = {'active', 'accepted', 'in_progress', 'completed', 'cancelled', 'closed'}
    if payload.status not in allowed:
        raise HTTPException(status_code=400, detail='Unsupported status')
    async with async_session() as session:
        row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == route_id))
        if not row:
            raise HTTPException(status_code=404, detail='Route not found')
        if current_user.tg_id not in {row.creator_tg_id, row.accepted_by_tg_id}:
            raise HTTPException(status_code=403, detail='Forbidden')
        row.status = payload.status
        if payload.status == 'completed':
            driver = await session.scalar(select(User).where(User.tg_id == row.creator_tg_id))
            if driver and driver.is_verified:
                driver.commission_due = 0.0
        await session.commit()
        return {'id': row.id, 'status': row.status}


@app.post('/intercity/requests/{request_id}/status')
async def intercity_request_status(request_id: int, payload: IntercityStatusUpdateRequest, current_user: User = Depends(get_current_user)) -> dict:
    allowed = {'active', 'accepted', 'in_progress', 'completed', 'cancelled', 'closed'}
    if payload.status not in allowed:
        raise HTTPException(status_code=400, detail='Unsupported status')
    async with async_session() as session:
        row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == request_id))
        if not row:
            raise HTTPException(status_code=404, detail='Request not found')
        if current_user.tg_id not in {row.creator_tg_id, row.accepted_by_tg_id}:
            raise HTTPException(status_code=403, detail='Forbidden')
        row.status = payload.status
        await session.commit()
        return {'id': row.id, 'status': row.status}


@app.get('/history/all', response_model=HistoryResponse)
async def history_all(current_user: User = Depends(get_current_user)) -> HistoryResponse:
    async with async_session() as session:
        city_orders = (await session.scalars(select(CityOrderV1).where(CityOrderV1.creator_tg_id == current_user.tg_id).order_by(CityOrderV1.id.desc()).limit(30))).all()
        city_trips = (await session.scalars(select(CityTripV1).where(or_(CityTripV1.passenger_tg_id == current_user.tg_id, CityTripV1.driver_tg_id == current_user.tg_id)).order_by(CityTripV1.id.desc()).limit(30))).all()
        routes = (await session.scalars(select(IntercityRouteV1).where(IntercityRouteV1.creator_tg_id == current_user.tg_id).order_by(IntercityRouteV1.id.desc()).limit(30))).all()
        requests = (await session.scalars(select(IntercityRequestV1).where(IntercityRequestV1.creator_tg_id == current_user.tg_id).order_by(IntercityRequestV1.id.desc()).limit(30))).all()
    return HistoryResponse(
        city_orders=[await _city_order_to_schema(row, current_user) for row in city_orders],
        city_trips=[await _city_trip_to_schema(row) for row in city_trips],
        intercity_routes=[IntercityOwnRouteResponse(id=row.id, country=row.country, from_city=row.from_city, to_city=row.to_city, date=row.departure_date, time=row.departure_time, seats=row.seats, price=row.price, comment=row.comment, status=row.status, created_at=_iso(row.created_at), pickup_mode=(await _intercity_offer_from_route(row, current_user)).pickup_mode) for row in routes],
        intercity_requests=[IntercityOwnRequestResponse(id=row.id, country=row.country, from_city=row.from_city, to_city=row.to_city, date=row.desired_date, time=row.desired_time, seats_needed=row.seats_needed, price_offer=row.price_offer, comment=row.comment, status=row.status, created_at=_iso(row.created_at)) for row in requests],
    )
