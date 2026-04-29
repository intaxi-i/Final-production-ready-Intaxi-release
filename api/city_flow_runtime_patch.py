from __future__ import annotations

from datetime import datetime, timezone
from math import ceil
from typing import Any, Callable

from fastapi import Depends, FastAPI, HTTPException, Query
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
    CityTripResponse,
    CityTripStatusUpdateRequest,
    CurrentTripResponse,
    DriverLocationUpdateRequest,
    DriverOnlineStateResponse,
    DriverOnlineUpdateRequest,
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
    utcnow,
)
from intaxi_bot.app.database.requests import DEFAULT_TARIFFS, haversine_km

LIVE_CITY_STATUSES = {"accepted", "driver_on_way", "driver_arrived", "in_progress"}
FINAL_CITY_STATUSES = {"completed", "cancelled", "closed", "cancelled_by_admin"}
CITY_STATUS_NEXT = {
    "accepted": {"driver_on_way", "driver_arrived", "cancelled"},
    "driver_on_way": {"driver_arrived", "cancelled"},
    "driver_arrived": {"in_progress", "cancelled"},
    "in_progress": {"completed", "cancelled"},
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


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


async def _vehicle_for_driver(session, driver_tg_id: int) -> Vehicle | None:
    driver = await session.scalar(select(User).where(User.tg_id == driver_tg_id))
    if not driver:
        return None
    return await session.scalar(select(Vehicle).where(Vehicle.user_id == driver.id))


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


async def _online_state(session, driver_tg_id: int) -> DriverOnlineState | None:
    return await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == driver_tg_id))


async def _ensure_online_state(session, driver: User) -> DriverOnlineState:
    row = await _online_state(session, driver.tg_id)
    if not row:
        row = DriverOnlineState(driver_tg_id=driver.tg_id, is_online=False, country=driver.country, city=driver.city)
        session.add(row)
        await session.flush()
    return row


async def _driver_has_live_trip(session, driver_tg_id: int) -> bool:
    trip = await session.scalar(
        select(CityTripV1)
        .where(CityTripV1.driver_tg_id == driver_tg_id, CityTripV1.status.in_(list(LIVE_CITY_STATUSES)))
        .order_by(CityTripV1.id.desc())
    )
    return trip is not None


async def _active_driver_candidates(session, *, country: str | None, city: str | None, from_lat: float | None = None, from_lng: float | None = None) -> list[tuple[float | None, User, DriverOnlineState]]:
    online_rows = (await session.scalars(select(DriverOnlineState).where(DriverOnlineState.is_online == True))).all()
    candidates: list[tuple[float | None, User, DriverOnlineState]] = []
    for row in online_rows:
        if not _same_or_empty(row.country, country) or not _same_or_empty(row.city, city):
            continue
        driver = await session.scalar(select(User).where(User.tg_id == row.driver_tg_id))
        if not driver or not driver.is_verified or _clean(driver.active_role) != "driver":
            continue
        if await _driver_has_live_trip(session, driver.tg_id):
            continue
        distance = None
        if from_lat is not None and from_lng is not None and row.lat is not None and row.lng is not None:
            distance = round(haversine_km(float(from_lat), float(from_lng), float(row.lat), float(row.lng)), 2)
        candidates.append((distance, driver, row))
    candidates.sort(key=lambda item: (item[0] is None, item[0] or 10**9))
    return candidates


async def _dispatch_stage_and_seen(session, *, country: str | None, city: str | None, from_lat: float | None, from_lng: float | None) -> tuple[str, int, float | None, int | None]:
    candidates = await _active_driver_candidates(session, country=country, city=city, from_lat=from_lat, from_lng=from_lng)
    if not candidates:
        return "manual_list", 0, None, None
    nearest = candidates[0][0]
    if nearest is None:
        return "active_drivers", len(candidates), None, None
    eta = max(2, ceil(nearest / 0.45))
    for threshold in (3, 6, 12, 15):
        count = sum(1 for distance, _, _ in candidates if distance is not None and distance <= threshold)
        if count:
            return f"{threshold}km", count, nearest, eta
    return "all_online", len(candidates), nearest, eta


def _map_provider(country: str | None) -> str:
    return "yandex" if country in {"uz", "tr"} else "google"


def _map_urls(country: str | None, lat: float | None, lng: float | None, to_lat: float | None = None, to_lng: float | None = None):
    provider = _map_provider(country)
    if lat is None or lng is None:
        return provider, None, None
    if provider == "yandex":
        return provider, f"https://yandex.com/map-widget/v1/?ll={lng}%2C{lat}&z=12&pt={lng},{lat},pm2rdm", f"https://yandex.com/maps/?ll={lng},{lat}&z=12&pt={lng},{lat},pm2rdm"
    query = f"{lat},{lng}"
    action = f"https://www.google.com/maps/dir/?api=1&origin={lat},{lng}&destination={to_lat},{to_lng}" if to_lat is not None and to_lng is not None else f"https://www.google.com/maps?q={query}"
    return provider, f"https://maps.google.com/maps?q={query}&z=12&output=embed", action


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
    elif runtime and runtime.active_trip_id:
        trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == runtime.active_trip_id))
        if trip and runtime.from_lat is not None and runtime.from_lng is not None and trip.driver_lat is not None and trip.driver_lng is not None:
            driver_distance = round(haversine_km(float(runtime.from_lat), float(runtime.from_lng), float(trip.driver_lat), float(trip.driver_lng)), 2)
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
    provider, embed, action = _map_urls(trip.country, trip.pickup_lat, trip.pickup_lng, trip.destination_lat, trip.destination_lng)
    eta = None
    if trip.driver_lat is not None and trip.driver_lng is not None and trip.pickup_lat is not None and trip.pickup_lng is not None:
        eta = max(2, ceil(haversine_km(float(trip.driver_lat), float(trip.driver_lng), float(trip.pickup_lat), float(trip.pickup_lng)) / 0.45))
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
        map_provider=provider,
        map_embed_url=embed,
        map_action_url=action,
        eta_min=eta,
    )


async def city_driver_online(current_user: User = Depends(get_current_user)) -> DriverOnlineStateResponse:
    async with async_session() as session:
        driver = await session.scalar(select(User).where(User.tg_id == current_user.tg_id))
        if not driver:
            raise HTTPException(status_code=404, detail="User not found")
        row = await _ensure_online_state(session, driver)
        return DriverOnlineStateResponse(is_online=bool(row.is_online), lat=row.lat, lng=row.lng, updated_at=row.updated_at.replace(microsecond=0).isoformat() if row.updated_at else None)


async def set_city_driver_online(payload: DriverOnlineUpdateRequest, current_user: User = Depends(get_current_user)) -> DriverOnlineStateResponse:
    if not current_user.is_verified or _clean(current_user.active_role) != "driver":
        raise HTTPException(status_code=403, detail="Only verified drivers in driver mode can go online")
    async with async_session() as session:
        driver = await session.scalar(select(User).where(User.tg_id == current_user.tg_id))
        if not driver:
            raise HTTPException(status_code=404, detail="User not found")
        row = await _ensure_online_state(session, driver)
        row.is_online = bool(payload.is_online)
        row.country = driver.country
        row.city = driver.city
        row.updated_at = _now()
        await session.commit()
        await session.refresh(row)
        return DriverOnlineStateResponse(is_online=bool(row.is_online), lat=row.lat, lng=row.lng, updated_at=row.updated_at.replace(microsecond=0).isoformat() if row.updated_at else None)


async def create_city_order(payload: CityOrderCreateRequest, current_user: User = Depends(get_current_user)) -> CityOrderCreateResponse:
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
        stage, seen, _, _ = await _dispatch_stage_and_seen(session, country=country, city=city, from_lat=payload.from_lat, from_lng=payload.from_lng)
        runtime = CityOrderRuntime(order_id=order.id, currency=currency, tariff_hint=hint, recommended_price=recommended_price, system_price=recommended_price, from_lat=payload.from_lat, from_lng=payload.from_lng, to_lat=payload.to_lat, to_lng=payload.to_lng, estimated_distance_km=distance, estimated_trip_min=eta, dispatch_stage=stage, seen_by_drivers=seen)
        session.add(runtime)
        await session.commit()
        await session.refresh(order)
        await session.refresh(runtime)
        return CityOrderCreateResponse(id=order.id, status=order.status, recommended_price=runtime.recommended_price, seen_by_drivers=runtime.seen_by_drivers, currency=runtime.currency, tariff_hint=runtime.tariff_hint)


async def city_offers(kind: str = Query("all"), current_user: User = Depends(get_current_user)) -> CityOrderListResponse:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == current_user.tg_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        driver_state = await _online_state(session, user.tg_id)
        wanted = kind if kind in {"driver", "passenger"} else None
        if _clean(user.active_role) == "driver":
            if not user.is_verified or not driver_state or not driver_state.is_online:
                return CityOrderListResponse(items=[])
            wanted = "passenger"
        rows = (await session.scalars(select(CityOrderV1).where(CityOrderV1.status == "active").order_by(CityOrderV1.id.desc()).limit(80))).all()
        items = []
        for order in rows:
            if order.creator_tg_id == user.tg_id or (wanted and order.role != wanted):
                continue
            if _clean(user.active_role) == "driver" and (not _same_or_empty(order.country, user.country) or not _same_or_empty(order.city, user.city)):
                continue
            runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
            if runtime and runtime.active_trip_id:
                continue
            items.append(await _order_schema(session, order, user, driver_state))
        items.sort(key=lambda item: (item.active_trip_id is not None, item.driver_distance_km is None, item.driver_distance_km or 10**9, -(item.id or 0)))
        return CityOrderListResponse(items=items[:30])


async def city_offer_detail(order_id: int | None = None, id: int | None = None, current_user: User = Depends(get_current_user)) -> CityOrderEnvelope:
    target_id = order_id if order_id is not None else id
    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == target_id))
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        driver_state = await _online_state(session, current_user.tg_id)
        return CityOrderEnvelope(item=await _order_schema(session, order, current_user, driver_state))


async def accept_city_offer(order_id: int | None = None, id: int | None = None, current_user: User = Depends(get_current_user)) -> CityAcceptResponse:
    target_id = order_id if order_id is not None else id
    async with async_session() as session:
        driver = await session.scalar(select(User).where(User.tg_id == current_user.tg_id))
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == target_id))
        if not driver or not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.role != "passenger" or order.creator_tg_id == driver.tg_id:
            raise HTTPException(status_code=403, detail="Only passenger orders can be accepted by drivers")
        if order.status != "active":
            raise HTTPException(status_code=409, detail="Order is already taken")
        if not driver.is_verified or _clean(driver.active_role) != "driver":
            raise HTTPException(status_code=403, detail="Only verified drivers in driver mode can accept city orders")
        online = await _online_state(session, driver.tg_id)
        if not online or not online.is_online:
            raise HTTPException(status_code=403, detail="Driver must be online to accept city orders")
        if not _same_or_empty(online.country, order.country) or not _same_or_empty(online.city, order.city):
            raise HTTPException(status_code=403, detail="Order is outside the driver's active city")
        if await _driver_has_live_trip(session, driver.tg_id):
            raise HTTPException(status_code=409, detail="Driver already has an active city trip")
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
        await session.refresh(trip)
        return CityAcceptResponse(trip_id=trip.id, status=trip.status)


async def city_my_orders(current_user: User = Depends(get_current_user)) -> CityOrderListResponse:
    async with async_session() as session:
        rows = (await session.scalars(select(CityOrderV1).where(CityOrderV1.creator_tg_id == current_user.tg_id).order_by(CityOrderV1.id.desc()).limit(30))).all()
        items = []
        for order in rows:
            runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
            if order.status == "active" and runtime:
                _, seen, _, _ = await _dispatch_stage_and_seen(session, country=order.country, city=order.city, from_lat=runtime.from_lat, from_lng=runtime.from_lng)
                runtime.seen_by_drivers = seen
                await session.flush()
            items.append(await _order_schema(session, order, current_user))
        await session.commit()
        return CityOrderListResponse(items=items)


async def city_trip_detail(trip_id: int | None = None, id: int | None = None, current_user: User = Depends(get_current_user)) -> CityTripEnvelope:
    target_id = trip_id if trip_id is not None else id
    async with async_session() as session:
        trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == target_id))
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        if current_user.tg_id not in {trip.passenger_tg_id, trip.driver_tg_id}:
            raise HTTPException(status_code=403, detail="Forbidden")
        return CityTripEnvelope(item=await _trip_schema(session, trip))


async def update_city_trip_status(trip_id: int | None = None, id: int | None = None, payload: CityTripStatusUpdateRequest | None = None, current_user: User = Depends(get_current_user)) -> CityTripEnvelope:
    target_id = trip_id if trip_id is not None else id
    target_status = payload.status if payload else None
    if target_status not in LIVE_CITY_STATUSES | FINAL_CITY_STATUSES:
        raise HTTPException(status_code=400, detail="Unsupported city trip status")
    async with async_session() as session:
        trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == target_id))
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        if current_user.tg_id != trip.driver_tg_id:
            raise HTTPException(status_code=403, detail="Only the driver can update city trip status")
        if target_status != trip.status and target_status not in CITY_STATUS_NEXT.get(trip.status, set()):
            raise HTTPException(status_code=409, detail="Invalid city trip status transition")
        trip.status = target_status
        trip.updated_at = _now()
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == trip.order_id))
        if target_status == "completed":
            trip.completed_at = _now()
            if order:
                order.status = "completed"
        elif target_status == "cancelled":
            trip.cancelled_at = _now()
            if order:
                order.status = "cancelled"
        await session.commit()
        await session.refresh(trip)
        return CityTripEnvelope(item=await _trip_schema(session, trip))


async def current_trip(original_endpoint: Callable | None = None, current_user: User = Depends(get_current_user)) -> CurrentTripResponse:
    async with async_session() as session:
        trip = await session.scalar(
            select(CityTripV1)
            .where(or_(CityTripV1.passenger_tg_id == current_user.tg_id, CityTripV1.driver_tg_id == current_user.tg_id), CityTripV1.status.in_(list(LIVE_CITY_STATUSES)))
            .order_by(CityTripV1.id.desc())
        )
        if trip:
            return CurrentTripResponse(item=(await _trip_schema(session, trip)).model_dump())
    if original_endpoint:
        return await original_endpoint(current_user=current_user)
    return CurrentTripResponse(item=None)


async def update_driver_location(payload: DriverLocationUpdateRequest, current_user: User = Depends(get_current_user)) -> dict[str, str]:
    async with async_session() as session:
        driver = await session.scalar(select(User).where(User.tg_id == current_user.tg_id))
        if not driver or not driver.is_verified:
            raise HTTPException(status_code=403, detail="Only verified drivers can update location")
        state = await _ensure_online_state(session, driver)
        state.lat = payload.lat
        state.lng = payload.lng
        state.country = driver.country
        state.city = driver.city
        state.updated_at = _now()
        if payload.trip_id:
            trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == payload.trip_id, CityTripV1.driver_tg_id == driver.tg_id))
            if trip and trip.status in LIVE_CITY_STATUSES:
                trip.driver_lat = payload.lat
                trip.driver_lng = payload.lng
                trip.updated_at = _now()
        await session.commit()
        return {"status": "ok", "updated_at": state.updated_at.replace(microsecond=0).isoformat()}


def _replacement(path: str, methods: Any, original_endpoint: Callable) -> Callable | None:
    method_set = {str(item).upper() for item in (methods or [])}
    if path == "/driver/online" and "GET" in method_set:
        return city_driver_online
    if path == "/driver/online" and "POST" in method_set:
        return set_city_driver_online
    if path == "/driver/location" and "POST" in method_set:
        return update_driver_location
    if path == "/city/orders" and "POST" in method_set:
        return create_city_order
    if path == "/city/offers" and "GET" in method_set:
        return city_offers
    if path.startswith("/city/offers/") and path.endswith("/accept") and "POST" in method_set:
        return accept_city_offer
    if path.startswith("/city/offers/") and "GET" in method_set:
        return city_offer_detail
    if path == "/city/my-orders" and "GET" in method_set:
        return city_my_orders
    if path.startswith("/city/trips/") and path.endswith("/status") and "POST" in method_set:
        return update_city_trip_status
    if path.startswith("/city/trips/") and "GET" in method_set:
        return city_trip_detail
    if path == "/trip/current" and "GET" in method_set:
        async def wrapped_current_trip(current_user: User = Depends(get_current_user)) -> CurrentTripResponse:
            return await current_trip(original_endpoint, current_user)
        return wrapped_current_trip
    return None


def install_city_flow_runtime_patch() -> None:
    if getattr(FastAPI, "_intaxi_city_flow_patch_installed", False):
        return
    original_add_api_route = FastAPI.add_api_route

    def patched_add_api_route(self, path: str, endpoint: Callable, *args: Any, **kwargs: Any):
        replacement = _replacement(path, kwargs.get("methods"), endpoint)
        if replacement is not None:
            endpoint = replacement
        return original_add_api_route(self, path, endpoint, *args, **kwargs)

    FastAPI.add_api_route = patched_add_api_route
    setattr(FastAPI, "_intaxi_city_flow_patch_installed", True)
