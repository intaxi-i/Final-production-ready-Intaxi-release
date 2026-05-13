from __future__ import annotations

from math import ceil
from typing import Any, Callable

from aiogram import Bot
from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy import or_, select

from api.auth import get_bot_token, get_current_user
from api.schemas import (
    CityAcceptResponse,
    CityOrderCreateRequest,
    CityOrderCreateResponse,
    CityOrderEnvelope,
    CityOrderListResponse,
    CityOrderResponse,
    CityTripEnvelope,
    CityTripResponse,
    CurrentTripResponse,
    DriverOnlineStateResponse,
    RaisePriceRequest,
    VehicleInfo,
)
from intaxi_bot.app.database.models import (
    CityOrderRuntime,
    CityOrderV1,
    CityTripV1,
    DriverOnlineState,
    TariffSetting,
    User,
    Vehicle,
    async_session,
)
from intaxi_bot.app.database.requests import DEFAULT_TARIFFS, haversine_km

LIVE_CITY_STATUSES = {"accepted", "driver_on_way", "driver_arrived", "in_progress"}
CITY_RADIUS_STAGES_KM = (3, 6, 12, 15)


async def _current_user(authorization: str | None = Header(default=None)) -> User:
    return await get_current_user(authorization)


def _clean(value: Any) -> str:
    return str(value or "").strip().lower()


def _same_or_empty(left: Any, right: Any) -> bool:
    left_value = _clean(left)
    right_value = _clean(right)
    return not left_value or not right_value or left_value == right_value


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


async def _tariff(country: str | None) -> tuple[str, float]:
    key = _clean(country) or "uz"
    async with async_session() as session:
        row = await session.scalar(select(TariffSetting).where(TariffSetting.country == key))
        if row:
            return row.currency, float(row.price_per_km or 0)
    currency, price = DEFAULT_TARIFFS.get(key, ("USD", 1.0))
    return currency, float(price or 0)


async def _recommended(country: str | None, from_lat: float | None, from_lng: float | None, to_lat: float | None, to_lng: float | None) -> tuple[float | None, float | None, int | None, str, str]:
    currency, price_per_km = await _tariff(country)
    hint = f"~{price_per_km:g} {currency}/km"
    if None in (from_lat, from_lng, to_lat, to_lng):
        return None, None, None, currency, hint
    distance = haversine_km(float(from_lat), float(from_lng), float(to_lat), float(to_lng))
    eta = max(3, ceil(distance / 0.45))
    return round(distance * price_per_km, 2), round(distance, 2), eta, currency, hint


async def _vehicle_for_driver(session, driver_tg_id: int) -> Vehicle | None:
    driver = await session.scalar(select(User).where(User.tg_id == driver_tg_id))
    if not driver:
        return None
    return await session.scalar(select(Vehicle).where(Vehicle.user_id == driver.id))


async def _driver_has_live_trip(session, driver_tg_id: int) -> bool:
    trip = await session.scalar(
        select(CityTripV1)
        .where(CityTripV1.driver_tg_id == driver_tg_id, CityTripV1.status.in_(list(LIVE_CITY_STATUSES)))
        .order_by(CityTripV1.id.desc())
    )
    return trip is not None


async def _active_driver_candidates(session, *, country: str | None, city: str | None, from_lat: float | None, from_lng: float | None) -> list[tuple[float | None, User, DriverOnlineState]]:
    rows = (await session.scalars(select(DriverOnlineState).where(DriverOnlineState.is_online == True))).all()
    candidates: list[tuple[float | None, User, DriverOnlineState]] = []
    for state in rows:
        if not _same_or_empty(state.country, country) or not _same_or_empty(state.city, city):
            continue
        driver = await session.scalar(select(User).where(User.tg_id == state.driver_tg_id))
        if not driver or not driver.is_verified or _clean(driver.active_role) != "driver":
            continue
        if await _driver_has_live_trip(session, driver.tg_id):
            continue
        distance = None
        if from_lat is not None and from_lng is not None and state.lat is not None and state.lng is not None:
            distance = round(haversine_km(float(from_lat), float(from_lng), float(state.lat), float(state.lng)), 2)
        candidates.append((distance, driver, state))
    candidates.sort(key=lambda item: (item[0] is None, item[0] or 10**9))
    return candidates


def _select_dispatch_stage(candidates: list[tuple[float | None, User, DriverOnlineState]]) -> tuple[str, list[tuple[float | None, User, DriverOnlineState]]]:
    if not candidates:
        return "manual_list", []
    with_distance = [item for item in candidates if item[0] is not None]
    if not with_distance:
        return "active_drivers", candidates
    for radius in CITY_RADIUS_STAGES_KM:
        selected = [item for item in with_distance if item[0] is not None and item[0] <= radius]
        if selected:
            return f"{radius}km", selected
    return "all_online", with_distance


async def _order_schema(session, order: CityOrderV1, current_user: User | None = None, driver_state: DriverOnlineState | None = None) -> CityOrderResponse:
    runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
    creator = await session.scalar(select(User).where(User.tg_id == order.creator_tg_id))
    vehicle = None
    if order.role == "driver" and creator:
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == creator.id))
    driver_distance = None
    driver_eta = None
    if driver_state and runtime and runtime.from_lat is not None and runtime.from_lng is not None and driver_state.lat is not None and driver_state.lng is not None:
        driver_distance = round(haversine_km(float(runtime.from_lat), float(runtime.from_lng), float(driver_state.lat), float(driver_state.lng)), 2)
        driver_eta = max(2, ceil(driver_distance / 0.45))
    return CityOrderResponse(
        id=order.id,
        creator_tg_id=order.creator_tg_id,
        creator_name=creator.full_name if creator else None,
        creator_rating=float(creator.rating or 0) if creator else None,
        role=order.role,
        country=order.country,
        city=order.city,
        from_address=order.from_address,
        to_address=order.to_address,
        seats=order.seats,
        price=float(order.price or 0),
        recommended_price=float(runtime.recommended_price) if runtime and runtime.recommended_price is not None else None,
        seen_by_drivers=int(runtime.seen_by_drivers) if runtime else 0,
        can_raise_price_after=30,
        estimated_distance_km=float(runtime.estimated_distance_km) if runtime and runtime.estimated_distance_km is not None else None,
        estimated_trip_min=int(runtime.estimated_trip_min) if runtime and runtime.estimated_trip_min is not None else None,
        driver_distance_km=driver_distance,
        driver_eta_min=driver_eta,
        comment=order.comment,
        status=order.status,
        created_at=str(order.created_at) if order.created_at else None,
        is_mine=bool(current_user and current_user.tg_id == order.creator_tg_id),
        active_trip_id=int(runtime.active_trip_id) if runtime and runtime.active_trip_id else None,
        vehicle=_vehicle_to_schema(vehicle),
        currency=runtime.currency if runtime else None,
        tariff_hint=runtime.tariff_hint if runtime else None,
    )


async def _trip_schema(session, trip: CityTripV1) -> CityTripResponse:
    passenger = await session.scalar(select(User).where(User.tg_id == trip.passenger_tg_id))
    driver = await session.scalar(select(User).where(User.tg_id == trip.driver_tg_id))
    vehicle = await _vehicle_for_driver(session, trip.driver_tg_id)
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
        driver_rating=float(driver.rating or 0) if driver else None,
        vehicle=_vehicle_to_schema(vehicle),
        trip_type="city_trip",
        pickup_lat=trip.pickup_lat,
        pickup_lng=trip.pickup_lng,
        destination_lat=trip.destination_lat,
        destination_lng=trip.destination_lng,
        driver_lat=trip.driver_lat,
        driver_lng=trip.driver_lng,
        passenger_lat=trip.passenger_lat,
        passenger_lng=trip.passenger_lng,
        eta_min=None,
    )


async def _notify_city_drivers(order_id: int) -> int:
    token = get_bot_token()
    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id))
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order_id))
        if not order or not runtime or order.role != "passenger" or order.status != "active":
            return 0
        candidates = await _active_driver_candidates(session, country=order.country, city=order.city, from_lat=runtime.from_lat, from_lng=runtime.from_lng)
        stage, selected = _select_dispatch_stage(candidates)
        runtime.dispatch_stage = stage
        runtime.seen_by_drivers = len(selected)
        await session.commit()
        payload = [(driver.tg_id, distance) for distance, driver, _ in selected]
        text = (
            "🆕 Новый городской заказ\n\n"
            f"A: {order.from_address or '—'}\n"
            f"B: {order.to_address or '—'}\n"
            f"Цена пассажира: {float(order.price or 0):g}\n"
            f"Мест: {int(order.seats or 1)}\n"
            f"Дистанция поездки: {float(runtime.estimated_distance_km):.1f} км\n" if runtime.estimated_distance_km is not None else "🆕 Новый городской заказ\n\n"
        )
    if not token or not payload:
        return len(payload)
    bot = Bot(token=token)
    try:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        for driver_tg_id, distance in payload:
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Принять заказ", callback_data=f"lccacc_{order_id}")
            builder.button(text="💰 Предложить свою цену", callback_data=f"lccoffer_{order_id}")
            builder.adjust(1)
            distance_line = f"\nДо пассажира: {float(distance):.1f} км" if distance is not None else ""
            try:
                await bot.send_message(driver_tg_id, text + distance_line, reply_markup=builder.as_markup())
            except Exception:
                pass
    finally:
        await bot.session.close()
    return len(payload)


async def create_city_order(payload: CityOrderCreateRequest, current_user: User = Depends(_current_user)) -> CityOrderCreateResponse:
    if payload.role != "passenger" or _clean(current_user.active_role) == "driver":
        raise HTTPException(status_code=403, detail="City order creation is available only in passenger mode")
    country = _clean(payload.country) or _clean(current_user.country) or "uz"
    city = str(payload.city or current_user.city or "").strip()
    recommended_price, distance, eta, currency, hint = await _recommended(country, payload.from_lat, payload.from_lng, payload.to_lat, payload.to_lng)
    final_price = float(payload.price) if payload.price is not None and float(payload.price) > 0 else recommended_price or payload.recommended_price
    if final_price is None or float(final_price) <= 0:
        raise HTTPException(status_code=400, detail="Price or valid route coordinates are required")
    async with async_session() as session:
        order = CityOrderV1(creator_tg_id=current_user.tg_id, role="passenger", country=country, city=city, from_address=payload.from_address, to_address=payload.to_address, seats=max(1, int(payload.seats or 1)), price=float(final_price), comment=payload.comment or "", status="active")
        session.add(order)
        await session.flush()
        runtime = CityOrderRuntime(order_id=order.id, currency=currency, tariff_hint=hint, recommended_price=recommended_price, system_price=recommended_price, from_lat=payload.from_lat, from_lng=payload.from_lng, to_lat=payload.to_lat, to_lng=payload.to_lng, estimated_distance_km=distance, estimated_trip_min=eta, dispatch_stage="manual_list", seen_by_drivers=0)
        session.add(runtime)
        await session.commit()
        order_id = order.id
    seen = await _notify_city_drivers(order_id)
    return CityOrderCreateResponse(id=order_id, status="active", recommended_price=recommended_price, seen_by_drivers=seen, currency=currency, tariff_hint=hint)


async def city_available_orders(current_user: User = Depends(_current_user)) -> CityOrderListResponse:
    if not current_user.is_verified or _clean(current_user.active_role) != "driver":
        raise HTTPException(status_code=403, detail="Only verified drivers can view available city orders")
    async with async_session() as session:
        state = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == current_user.tg_id))
        if not state or not state.is_online:
            return CityOrderListResponse(items=[])
        rows = (await session.scalars(select(CityOrderV1).where(CityOrderV1.status == "active", CityOrderV1.role == "passenger", CityOrderV1.creator_tg_id != current_user.tg_id).order_by(CityOrderV1.id.desc()).limit(80))).all()
        items = []
        for order in rows:
            if not _same_or_empty(order.country, state.country) or not _same_or_empty(order.city, state.city):
                continue
            items.append(await _order_schema(session, order, current_user, state))
        items.sort(key=lambda item: (item.driver_distance_km is None, item.driver_distance_km or 10**9, -(item.id or 0)))
        return CityOrderListResponse(items=items[:30])


async def city_my_orders(current_user: User = Depends(_current_user)) -> CityOrderListResponse:
    async with async_session() as session:
        rows = (await session.scalars(select(CityOrderV1).where(CityOrderV1.creator_tg_id == current_user.tg_id).order_by(CityOrderV1.id.desc()).limit(30))).all()
        return CityOrderListResponse(items=[await _order_schema(session, row, current_user) for row in rows])


async def accept_city_order(order_id: int, current_user: User = Depends(_current_user)) -> CityAcceptResponse:
    async with async_session() as session:
        driver = await session.scalar(select(User).where(User.tg_id == current_user.tg_id))
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id).with_for_update())
        if not driver or not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if not driver.is_verified or _clean(driver.active_role) != "driver":
            raise HTTPException(status_code=403, detail="Only verified drivers can accept city orders")
        if order.role != "passenger" or order.creator_tg_id == driver.tg_id:
            raise HTTPException(status_code=403, detail="Only passenger orders can be accepted by drivers")
        if order.status != "active":
            raise HTTPException(status_code=409, detail="Order is already taken")
        online = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == driver.tg_id))
        if not online or not online.is_online:
            raise HTTPException(status_code=403, detail="Driver must be online")
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
        if runtime and runtime.active_trip_id:
            raise HTTPException(status_code=409, detail="Order is already taken")
        trip = CityTripV1(order_id=order.id, status="accepted", price=float(order.price or 0), country=order.country, city=order.city, from_address=order.from_address, to_address=order.to_address, seats=order.seats, comment=order.comment, passenger_tg_id=order.creator_tg_id, driver_tg_id=driver.tg_id, pickup_lat=runtime.from_lat if runtime else None, pickup_lng=runtime.from_lng if runtime else None, destination_lat=runtime.to_lat if runtime else None, destination_lng=runtime.to_lng if runtime else None, driver_lat=online.lat, driver_lng=online.lng, passenger_lat=runtime.from_lat if runtime else None, passenger_lng=runtime.from_lng if runtime else None)
        session.add(trip)
        await session.flush()
        order.accepted_by_tg_id = driver.tg_id
        order.status = "accepted"
        if runtime:
            runtime.active_trip_id = trip.id
        await session.commit()
        return CityAcceptResponse(trip_id=trip.id, status=trip.status)


async def city_counteroffer(order_id: int, payload: RaisePriceRequest, current_user: User = Depends(_current_user)) -> dict[str, Any]:
    if not current_user.is_verified or _clean(current_user.active_role) != "driver":
        raise HTTPException(status_code=403, detail="Only verified drivers can send counteroffers")
    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id))
        if not order or order.status != "active":
            raise HTTPException(status_code=404, detail="Order not found")
        if order.creator_tg_id == current_user.tg_id or order.role != "passenger":
            raise HTTPException(status_code=403, detail="Counteroffer is not allowed for this order")
        passenger_tg_id = order.creator_tg_id
    token = get_bot_token()
    if token:
        bot = Bot(token=token)
        try:
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            price_int = int(float(payload.price))
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Принять цену", callback_data=f"lcpacc_{order_id}_{current_user.tg_id}_{price_int}")
            builder.button(text="❌ Отклонить", callback_data=f"lcprej_{order_id}_{current_user.tg_id}")
            builder.adjust(1)
            await bot.send_message(passenger_tg_id, f"💰 Водитель предложил свою цену: {float(payload.price):g}", reply_markup=builder.as_markup())
        finally:
            await bot.session.close()
    return {"id": order_id, "status": "sent", "price": float(payload.price)}


async def current_trip(current_user: User = Depends(_current_user)) -> CurrentTripResponse:
    async with async_session() as session:
        trip = await session.scalar(select(CityTripV1).where(or_(CityTripV1.passenger_tg_id == current_user.tg_id, CityTripV1.driver_tg_id == current_user.tg_id), CityTripV1.status.in_(list(LIVE_CITY_STATUSES))).order_by(CityTripV1.id.desc()))
        if trip:
            return CurrentTripResponse(item=(await _trip_schema(session, trip)).model_dump())
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.creator_tg_id == current_user.tg_id, CityOrderV1.status == "active", CityOrderV1.role == "passenger").order_by(CityOrderV1.id.desc()))
        if order:
            item = (await _order_schema(session, order, current_user)).model_dump()
            item["trip_type"] = "city_order"
            return CurrentTripResponse(item=item)
    return CurrentTripResponse(item=None)


def install_intaxi_production_patch() -> None:
    if getattr(FastAPI, "_intaxi_production_patch_installed", False):
        return
    original_add_api_route = FastAPI.add_api_route

    def patched_add_api_route(self, path: str, endpoint: Callable, *args: Any, **kwargs: Any):
        methods = {str(m).upper() for m in (kwargs.get("methods") or [])}
        replacement = None
        if path == "/city/orders" and "POST" in methods:
            replacement = create_city_order
        elif path == "/trip/current" and "GET" in methods:
            replacement = current_trip
        elif path == "/city/my-orders" and "GET" in methods:
            replacement = city_my_orders
        elif path.startswith("/city/offers/") and path.endswith("/accept") and "POST" in methods:
            replacement = accept_city_order
        endpoint_to_register = replacement or endpoint
        result = original_add_api_route(self, path, endpoint_to_register, *args, **kwargs)
        if path == "/city/offers" and "GET" in methods:
            original_add_api_route(self, "/city/orders/available", city_available_orders, methods=["GET"], response_model=CityOrderListResponse)
        elif path == "/city/my-orders" and "GET" in methods:
            original_add_api_route(self, "/city/orders/my", city_my_orders, methods=["GET"], response_model=CityOrderListResponse)
        elif path.startswith("/city/offers/") and path.endswith("/accept") and "POST" in methods:
            original_add_api_route(self, "/city/orders/{order_id}/accept", accept_city_order, methods=["POST"], response_model=CityAcceptResponse)
            original_add_api_route(self, "/city/orders/{order_id}/counteroffers", city_counteroffer, methods=["POST"])
        return result

    FastAPI.add_api_route = patched_add_api_route
    setattr(FastAPI, "_intaxi_production_patch_installed", True)
