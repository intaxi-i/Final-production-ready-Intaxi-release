from __future__ import annotations

import importlib
from math import ceil
from typing import Any

from sqlalchemy import select

LIVE_CITY_STATUSES = {"accepted", "driver_on_way", "driver_arrived", "in_progress"}
KZ_TARIFF = ("KZT", 120.0)


def _clean(value: Any) -> str:
    return str(value or "").strip().lower()


def _same_or_empty(left: Any, right: Any) -> bool:
    left_value = _clean(left)
    right_value = _clean(right)
    return not left_value or not right_value or left_value == right_value


def _load_modules(requests_module_name: str):
    req = importlib.import_module(requests_module_name)
    models = importlib.import_module(req.__package__ + ".models")
    return req, models


async def _online_state(models, session, driver_tg_id: int):
    return await session.scalar(select(models.DriverOnlineState).where(models.DriverOnlineState.driver_tg_id == driver_tg_id))


async def _driver_has_live_trip(models, session, driver_tg_id: int) -> bool:
    trip = await session.scalar(
        select(models.CityTripV1)
        .where(models.CityTripV1.driver_tg_id == driver_tg_id, models.CityTripV1.status.in_(list(LIVE_CITY_STATUSES)))
        .order_by(models.CityTripV1.id.desc())
    )
    return trip is not None


async def _active_driver_count(models, session, *, country: str | None, city: str | None) -> int:
    rows = (await session.scalars(select(models.DriverOnlineState).where(models.DriverOnlineState.is_online == True))).all()
    count = 0
    for row in rows:
        if not _same_or_empty(row.country, country) or not _same_or_empty(row.city, city):
            continue
        driver = await session.scalar(select(models.User).where(models.User.tg_id == row.driver_tg_id))
        if not driver or not driver.is_verified or _clean(driver.active_role) != "driver":
            continue
        if await _driver_has_live_trip(models, session, driver.tg_id):
            continue
        count += 1
    return count


def patch_requests_module(module_name: str) -> None:
    try:
        req, models = _load_modules(module_name)
    except Exception:
        return

    if getattr(req, "_intaxi_city_flow_helper_patch_installed", False):
        return

    if isinstance(getattr(req, "DEFAULT_TARIFFS", None), dict):
        req.DEFAULT_TARIFFS.setdefault("kz", KZ_TARIFF)

    async_session = models.async_session
    User = models.User
    Vehicle = models.Vehicle
    CityOrderV1 = models.CityOrderV1
    CityOrderRuntime = models.CityOrderRuntime
    CityTripV1 = models.CityTripV1
    haversine_km = req.haversine_km
    original_get_current_trip = getattr(req, "get_current_trip_for_user", None)

    async def create_city_order_bot(*, creator_tg_id: int, role: str, country: str, city: str, from_address: str, to_address: str, seats: int = 1, price: float | None = None, comment: str = "", from_lat: float | None = None, from_lng: float | None = None, to_lat: float | None = None, to_lng: float | None = None):
        if role != "passenger":
            raise ValueError("City bot orders can only be created by passengers")
        normalized_country = _clean(country) or "uz"
        normalized_city = str(city or "").strip()
        async with async_session() as session:
            user = await session.scalar(select(User).where(User.tg_id == creator_tg_id))
            if not user:
                raise ValueError("User not found")
            if _clean(user.active_role) == "driver":
                raise ValueError("Switch to passenger mode before creating a city order")
            tariff_helper = getattr(req, "_tariff_for_country", None)
            if tariff_helper:
                currency, tariff_per_km = await tariff_helper(session, normalized_country)
            else:
                currency, tariff_per_km = req.DEFAULT_TARIFFS.get(normalized_country, ("USD", 0.0))
            dist_km = None
            eta = None
            recommended_price = None
            if None not in {from_lat, from_lng, to_lat, to_lng}:
                dist_km = round(haversine_km(float(from_lat), float(from_lng), float(to_lat), float(to_lng)), 2)
                eta = max(3, ceil(dist_km / 0.45))
                recommended_price = round(dist_km * float(tariff_per_km or 0), 2)
            final_price = float(price) if price is not None and float(price) > 0 else recommended_price
            if final_price is None or final_price <= 0:
                raise ValueError("Price is required when distance cannot be calculated")
            order = CityOrderV1(creator_tg_id=creator_tg_id, role="passenger", country=normalized_country, city=normalized_city, from_address=from_address, to_address=to_address, seats=max(1, int(seats or 1)), price=final_price, comment=comment or "", status="active")
            session.add(order)
            await session.flush()
            seen = await _active_driver_count(models, session, country=normalized_country, city=normalized_city)
            runtime = CityOrderRuntime(order_id=order.id, currency=currency, tariff_hint=f"{currency} {tariff_per_km}/km", recommended_price=recommended_price, system_price=recommended_price, from_lat=from_lat, from_lng=from_lng, to_lat=to_lat, to_lng=to_lng, estimated_distance_km=dist_km, estimated_trip_min=eta, dispatch_stage="active_drivers" if seen else "manual_list", seen_by_drivers=int(seen))
            session.add(runtime)
            await session.commit()
            await session.refresh(order)
            await session.refresh(runtime)
            return order, runtime

    async def list_city_market_for_user(tg_id: int, *, wanted_role: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        async with async_session() as session:
            current_user = await session.scalar(select(User).where(User.tg_id == tg_id))
            if not current_user:
                return []
            role = _clean(current_user.active_role)
            driver_state = await _online_state(models, session, tg_id)
            if role == "driver":
                if not current_user.is_verified or not driver_state or not driver_state.is_online:
                    return []
                wanted_role = "passenger"
            rows = (await session.scalars(select(CityOrderV1).where(CityOrderV1.status == "active").order_by(CityOrderV1.id.desc()).limit(max(limit * 5, 25)))).all()
            result: list[dict[str, Any]] = []
            for row in rows:
                if row.creator_tg_id == tg_id:
                    continue
                if wanted_role and row.role != wanted_role:
                    continue
                if role == "driver" and (not _same_or_empty(row.country, current_user.country) or not _same_or_empty(row.city, current_user.city)):
                    continue
                runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == row.id))
                if runtime and runtime.active_trip_id:
                    continue
                creator = await session.scalar(select(User).where(User.tg_id == row.creator_tg_id))
                vehicle = None
                if row.role == "driver" and creator:
                    vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == creator.id))
                distance = None
                if driver_state and runtime and driver_state.lat is not None and driver_state.lng is not None and runtime.from_lat is not None and runtime.from_lng is not None:
                    distance = round(haversine_km(float(driver_state.lat), float(driver_state.lng), float(runtime.from_lat), float(runtime.from_lng)), 2)
                result.append({"order": row, "runtime": runtime, "creator": creator, "vehicle": vehicle, "driver_distance_km": distance})
            result.sort(key=lambda item: (item.get("driver_distance_km") is None, item.get("driver_distance_km") or 10**9, -int(item["order"].id)))
            return result[:limit]

    async def accept_city_offer_for_user(order_id: int, tg_id: int) -> CityTripV1 | None:
        async with async_session() as session:
            order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id))
            driver = await session.scalar(select(User).where(User.tg_id == tg_id))
            if not order or not driver or order.status != "active" or order.creator_tg_id == tg_id or order.role != "passenger":
                return None
            if not driver.is_verified or _clean(driver.active_role) != "driver":
                return None
            online = await _online_state(models, session, driver.tg_id)
            if not online or not online.is_online:
                return None
            if not _same_or_empty(online.country, order.country) or not _same_or_empty(online.city, order.city):
                return None
            if await _driver_has_live_trip(models, session, driver.tg_id):
                return None
            runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
            if runtime and runtime.active_trip_id:
                return None
            trip = CityTripV1(order_id=order.id, status="accepted", price=float(order.price or 0), country=order.country, city=order.city, from_address=order.from_address, to_address=order.to_address, seats=order.seats, comment=order.comment, passenger_tg_id=order.creator_tg_id, driver_tg_id=driver.tg_id, pickup_lat=runtime.from_lat if runtime else None, pickup_lng=runtime.from_lng if runtime else None, destination_lat=runtime.to_lat if runtime else None, destination_lng=runtime.to_lng if runtime else None, driver_lat=online.lat, driver_lng=online.lng, passenger_lat=runtime.from_lat if runtime else None, passenger_lng=runtime.from_lng if runtime else None)
            session.add(trip)
            await session.flush()
            order.accepted_by_tg_id = driver.tg_id
            order.status = "accepted"
            if runtime:
                runtime.active_trip_id = trip.id
            await session.commit()
            await session.refresh(trip)
            return trip

    async def get_current_trip_for_user(tg_id: int):
        async with async_session() as session:
            city_trip = await session.scalar(select(CityTripV1).where(((CityTripV1.passenger_tg_id == tg_id) | (CityTripV1.driver_tg_id == tg_id)), CityTripV1.status.in_(list(LIVE_CITY_STATUSES))).order_by(CityTripV1.id.desc()))
            if city_trip:
                return city_trip
        if original_get_current_trip:
            return await original_get_current_trip(tg_id)
        return None

    req.create_city_order_bot = create_city_order_bot
    req.list_city_market_for_user = list_city_market_for_user
    req.accept_city_offer_for_user = accept_city_offer_for_user
    req.get_current_trip_for_user = get_current_trip_for_user
    setattr(req, "_intaxi_city_flow_helper_patch_installed", True)


def install_city_flow_helper_patch() -> None:
    for module_name in ("app.database.requests", "intaxi_bot.app.database.requests"):
        patch_requests_module(module_name)
