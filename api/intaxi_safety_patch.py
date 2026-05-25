from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any, Callable

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import or_, select

from api.auth import get_current_user
from api.order_actions import close_city_order_for_user
from api.schemas import (
    CityOrderListResponse,
    CurrentTripResponse,
    DriverOnlineStateResponse,
    DriverOnlineUpdateRequest,
    HistoryResponse,
)
from api.services.lifecycle import find_current_city_order, find_current_city_trip, find_current_intercity_offer, LIVE_CITY_STATUSES
from intaxi_bot.app.database.models import (
    CityOrderRuntime,
    CityOrderV1,
    CityTripV1,
    DriverOnlineState,
    IntercityRequestV1,
    IntercityRouteMeta,
    IntercityRouteV1,
    User,
    Vehicle,
    async_session,
    utcnow,
)


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    return value.replace(microsecond=0).isoformat() if hasattr(value, 'replace') and hasattr(value, 'isoformat') else str(value)


def _clean(value: Any) -> str:
    return str(value or '').strip().lower()


def _same_or_empty(left: Any, right: Any) -> bool:
    left_value = _clean(left)
    right_value = _clean(right)
    return not left_value or not right_value or left_value == right_value


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return radius * 2 * asin(sqrt(a))


def _map_provider(country: str | None) -> str:
    return 'yandex' if country in {'uz', 'tr'} else 'google'


def _map_urls(country: str | None, lat: float | None, lng: float | None, to_lat: float | None = None, to_lng: float | None = None):
    provider = _map_provider(country)
    if lat is None or lng is None:
        return provider, None, None
    if provider == 'yandex':
        embed = f'https://yandex.com/map-widget/v1/?ll={lng}%2C{lat}&z=12&pt={lng},{lat},pm2rdm'
        action = f'https://yandex.com/maps/?rtext={lat},{lng}~{to_lat},{to_lng}&rtt=auto' if to_lat is not None and to_lng is not None else f'https://yandex.com/maps/?ll={lng},{lat}&z=12&pt={lng},{lat},pm2rdm'
        return provider, embed, action
    query = f'{lat},{lng}'
    action = f'https://www.google.com/maps/dir/?api=1&origin={lat},{lng}&destination={to_lat},{to_lng}' if to_lat is not None and to_lng is not None else f'https://www.google.com/maps?q={query}'
    return provider, f'https://maps.google.com/maps?q={query}&z=12&output=embed', action


def _vehicle_dict(vehicle: Vehicle | None) -> dict | None:
    if not vehicle:
        return None
    return {
        'brand': vehicle.brand,
        'model': vehicle.model,
        'plate': vehicle.plate,
        'color': vehicle.color,
        'capacity': vehicle.capacity,
        'vehicle_class': vehicle.vehicle_class,
    }


async def _driver_has_live_trip(session, driver_tg_id: int) -> bool:
    trip = await session.scalar(
        select(CityTripV1)
        .where(CityTripV1.driver_tg_id == driver_tg_id, CityTripV1.status.in_(list(LIVE_CITY_STATUSES)))
        .order_by(CityTripV1.id.desc())
    )
    return trip is not None


async def _ensure_online_state(session, driver: User) -> DriverOnlineState:
    row = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == driver.tg_id))
    if not row:
        row = DriverOnlineState(driver_tg_id=driver.tg_id, is_online=False, country=driver.country, city=driver.city)
        session.add(row)
        await session.flush()
    return row


async def safe_driver_online_update(payload: DriverOnlineUpdateRequest, current_user: User = Depends(get_current_user)) -> DriverOnlineStateResponse:
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail='Only verified drivers can use this feature')
    async with async_session() as session:
        row = await _ensure_online_state(session, current_user)
        row.is_online = bool(payload.is_online)
        row.country = payload.country_code or payload.country or current_user.country
        row.city = payload.city or current_user.city
        if payload.lat is not None:
            row.lat = payload.lat
        if payload.lng is not None:
            row.lng = payload.lng
        row.updated_at = utcnow()
        busy = await _driver_has_live_trip(session, current_user.tg_id)
        await session.commit()
        await session.refresh(row)
        return DriverOnlineStateResponse(
            is_online=row.is_online,
            lat=row.lat,
            lng=row.lng,
            country=row.country,
            city=row.city,
            is_busy=busy,
            updated_at=_iso(row.updated_at),
        )


async def safe_city_close(order_id: int, current_user: User = Depends(get_current_user)) -> dict:
    row = await close_city_order_for_user(order_id, current_user.tg_id)
    if not row:
        raise HTTPException(status_code=404, detail='Order not found')
    return {'id': row.id, 'status': row.status}


async def _city_order_item(session, row: CityOrderV1, current_user: User, driver_state: DriverOnlineState | None = None) -> dict:
    runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == row.id))
    creator = await session.scalar(select(User).where(User.tg_id == row.creator_tg_id))
    vehicle = None
    if row.role == 'driver' and creator:
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == creator.id))
    distance = None
    eta = None
    if driver_state and runtime and runtime.from_lat is not None and runtime.from_lng is not None and driver_state.lat is not None and driver_state.lng is not None:
        distance = round(_haversine_km(float(runtime.from_lat), float(runtime.from_lng), float(driver_state.lat), float(driver_state.lng)), 2)
        eta = max(2, int(distance / 0.45))
    return {
        'id': row.id,
        'creator_tg_id': row.creator_tg_id,
        'creator_name': creator.full_name if creator else None,
        'creator_rating': float(creator.rating or 0) if creator else None,
        'role': row.role,
        'country': row.country,
        'city': row.city or '',
        'from_address': row.from_address or '',
        'to_address': row.to_address,
        'seats': int(row.seats or 1),
        'price': float(row.price or 0),
        'recommended_price': float(runtime.recommended_price) if runtime and runtime.recommended_price is not None else None,
        'seen_by_drivers': int(runtime.seen_by_drivers) if runtime else None,
        'can_raise_price_after': 30,
        'estimated_distance_km': float(runtime.estimated_distance_km) if runtime and runtime.estimated_distance_km is not None else None,
        'estimated_trip_min': int(runtime.estimated_trip_min) if runtime and runtime.estimated_trip_min is not None else None,
        'driver_distance_km': distance,
        'driver_eta_min': eta,
        'comment': row.comment,
        'status': row.status,
        'created_at': _iso(row.created_at),
        'is_mine': current_user.tg_id == row.creator_tg_id,
        'active_trip_id': int(runtime.active_trip_id) if runtime and runtime.active_trip_id is not None else None,
        'vehicle': _vehicle_dict(vehicle),
        'currency': runtime.currency if runtime else None,
        'tariff_hint': runtime.tariff_hint if runtime else None,
    }


async def safe_city_offers(kind: str = Query('all'), current_user: User = Depends(get_current_user)) -> CityOrderListResponse:
    async with async_session() as session:
        driver_mode = bool(current_user.is_verified and _clean(current_user.active_role) == 'driver')
        driver_state = None
        wanted_role = None
        if driver_mode:
            driver_state = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == current_user.tg_id))
            if not driver_state or not driver_state.is_online or await _driver_has_live_trip(session, current_user.tg_id):
                return CityOrderListResponse(items=[])
            wanted_role = 'passenger'
        else:
            wanted_role = 'driver'

        if kind in {'driver', 'passenger'} and kind != wanted_role:
            return CityOrderListResponse(items=[])

        rows = (await session.scalars(
            select(CityOrderV1)
            .where(CityOrderV1.status == 'active', CityOrderV1.role == wanted_role, CityOrderV1.creator_tg_id != current_user.tg_id)
            .order_by(CityOrderV1.id.desc())
            .limit(100)
        )).all()
        items = []
        for row in rows:
            if driver_mode:
                if not _same_or_empty(row.country, driver_state.country) or not _same_or_empty(row.city, driver_state.city):
                    continue
            else:
                if not _same_or_empty(row.country, current_user.country) or not _same_or_empty(row.city, current_user.city):
                    continue
                creator = await session.scalar(select(User).where(User.tg_id == row.creator_tg_id))
                if not creator or not creator.is_verified:
                    continue
            items.append(await _city_order_item(session, row, current_user, driver_state))
    return CityOrderListResponse(items=items)


async def safe_current_trip(current_user: User = Depends(get_current_user)) -> CurrentTripResponse:
    async with async_session() as session:
        trip = await find_current_city_trip(session, current_user.tg_id)
        if trip:
            passenger = await session.scalar(select(User).where(User.tg_id == trip.passenger_tg_id))
            driver = await session.scalar(select(User).where(User.tg_id == trip.driver_tg_id))
            vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == driver.id)) if driver else None
            provider, embed, action = _map_urls(trip.country, trip.pickup_lat, trip.pickup_lng, trip.destination_lat, trip.destination_lng)
            return CurrentTripResponse(item={
                'id': trip.id, 'order_id': trip.order_id, 'trip_type': 'city_trip', 'status': trip.status,
                'price': float(trip.price or 0), 'country': trip.country, 'city': trip.city,
                'from_address': trip.from_address, 'to_address': trip.to_address, 'seats': trip.seats,
                'comment': trip.comment, 'passenger_tg_id': trip.passenger_tg_id, 'driver_tg_id': trip.driver_tg_id,
                'passenger_name': passenger.full_name if passenger else None,
                'passenger_username': passenger.username if passenger else None,
                'driver_name': driver.full_name if driver else None,
                'driver_username': driver.username if driver else None,
                'driver_rating': float(driver.rating or 0) if driver else None,
                'vehicle': _vehicle_dict(vehicle),
                'pickup_lat': trip.pickup_lat, 'pickup_lng': trip.pickup_lng,
                'destination_lat': trip.destination_lat, 'destination_lng': trip.destination_lng,
                'driver_lat': trip.driver_lat, 'driver_lng': trip.driver_lng,
                'passenger_lat': trip.passenger_lat, 'passenger_lng': trip.passenger_lng,
                'map_provider': provider, 'map_embed_url': embed, 'map_action_url': action,
            })

        order = await find_current_city_order(session, current_user.tg_id)
        if order:
            runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
            return CurrentTripResponse(item={
                'id': order.id, 'trip_type': 'city_order', 'status': order.status, 'price': float(order.price or 0),
                'country': order.country, 'city': order.city, 'from_address': order.from_address,
                'to_address': order.to_address, 'seats': order.seats, 'comment': order.comment,
                'creator_tg_id': order.creator_tg_id, 'is_mine': True,
                'active_trip_id': int(runtime.active_trip_id) if runtime and runtime.active_trip_id is not None else None,
                'currency': runtime.currency if runtime else None, 'tariff_hint': runtime.tariff_hint if runtime else None,
            })

        current_intercity = await find_current_intercity_offer(session, current_user.tg_id)
        if current_intercity:
            kind, item = current_intercity
            if kind == 'intercity_route':
                meta = await session.scalar(select(IntercityRouteMeta).where(IntercityRouteMeta.route_id == item.id))
                provider, embed, action = _map_urls(item.country, meta.meeting_lat if meta else None, meta.meeting_lng if meta else None)
                return CurrentTripResponse(item={
                    'id': item.id, 'trip_type': 'intercity_route', 'status': item.status, 'price': float(item.price or 0),
                    'country': item.country, 'from_city': item.from_city, 'to_city': item.to_city, 'comment': item.comment,
                    'pickup_mode': meta.pickup_mode if meta else 'ask_driver', 'map_provider': provider,
                    'map_embed_url': embed, 'map_action_url': action, 'date': item.departure_date,
                    'time': item.departure_time, 'seats': item.seats, 'accepted_by_tg_id': item.accepted_by_tg_id,
                    'creator_tg_id': item.creator_tg_id, 'is_mine': current_user.tg_id == item.creator_tg_id,
                })
            provider, embed, action = _map_urls(item.country, None, None)
            return CurrentTripResponse(item={
                'id': item.id, 'trip_type': 'intercity_request', 'status': item.status,
                'price': float(item.price_offer or 0), 'country': item.country, 'from_city': item.from_city,
                'to_city': item.to_city, 'comment': item.comment, 'map_provider': provider,
                'map_embed_url': embed, 'map_action_url': action, 'date': item.desired_date,
                'time': item.desired_time, 'seats': item.seats_needed, 'accepted_by_tg_id': item.accepted_by_tg_id,
                'creator_tg_id': item.creator_tg_id, 'is_mine': current_user.tg_id == item.creator_tg_id,
            })
    return CurrentTripResponse(item=None)


async def safe_history_all(current_user: User = Depends(get_current_user)) -> HistoryResponse:
    async with async_session() as session:
        city_orders = (await session.scalars(select(CityOrderV1).where(CityOrderV1.creator_tg_id == current_user.tg_id).order_by(CityOrderV1.id.desc()).limit(30))).all()
        city_trips = (await session.scalars(select(CityTripV1).where(or_(CityTripV1.passenger_tg_id == current_user.tg_id, CityTripV1.driver_tg_id == current_user.tg_id)).order_by(CityTripV1.id.desc()).limit(30))).all()
        routes = (await session.scalars(select(IntercityRouteV1).where(or_(IntercityRouteV1.creator_tg_id == current_user.tg_id, IntercityRouteV1.accepted_by_tg_id == current_user.tg_id)).order_by(IntercityRouteV1.id.desc()).limit(30))).all()
        requests = (await session.scalars(select(IntercityRequestV1).where(or_(IntercityRequestV1.creator_tg_id == current_user.tg_id, IntercityRequestV1.accepted_by_tg_id == current_user.tg_id)).order_by(IntercityRequestV1.id.desc()).limit(30))).all()

        city_order_items = []
        for row in city_orders:
            runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == row.id))
            city_order_items.append({
                'id': row.id, 'creator_tg_id': row.creator_tg_id, 'role': row.role or 'passenger',
                'country': row.country, 'city': row.city or '', 'from_address': row.from_address or '',
                'to_address': row.to_address, 'seats': int(row.seats or 1), 'price': float(row.price or 0),
                'comment': row.comment, 'status': row.status, 'created_at': _iso(row.created_at),
                'is_mine': current_user.tg_id == row.creator_tg_id,
                'active_trip_id': int(runtime.active_trip_id) if runtime and runtime.active_trip_id is not None else None,
                'currency': runtime.currency if runtime else None, 'tariff_hint': runtime.tariff_hint if runtime else None,
            })

        city_trip_items = []
        for trip in city_trips:
            city_trip_items.append({
                'id': trip.id, 'order_id': trip.order_id, 'status': trip.status or '', 'price': float(trip.price or 0),
                'country': trip.country, 'city': trip.city, 'from_address': trip.from_address, 'to_address': trip.to_address,
                'seats': trip.seats, 'comment': trip.comment, 'passenger_tg_id': trip.passenger_tg_id,
                'driver_tg_id': trip.driver_tg_id, 'trip_type': 'city_trip', 'pickup_lat': trip.pickup_lat,
                'pickup_lng': trip.pickup_lng, 'destination_lat': trip.destination_lat, 'destination_lng': trip.destination_lng,
                'driver_lat': trip.driver_lat, 'driver_lng': trip.driver_lng, 'passenger_lat': trip.passenger_lat,
                'passenger_lng': trip.passenger_lng,
            })

        route_items = []
        for row in routes:
            meta = await session.scalar(select(IntercityRouteMeta).where(IntercityRouteMeta.route_id == row.id))
            route_items.append({
                'id': row.id, 'country': row.country, 'from_city': row.from_city or '', 'to_city': row.to_city or '',
                'date': row.departure_date or '', 'time': row.departure_time or '', 'seats': int(row.seats or 1),
                'price': float(row.price or 0), 'comment': row.comment, 'status': row.status,
                'created_at': _iso(row.created_at), 'pickup_mode': meta.pickup_mode if meta else 'ask_driver',
            })

        request_items = [{
            'id': row.id, 'country': row.country, 'from_city': row.from_city or '', 'to_city': row.to_city or '',
            'date': row.desired_date or '', 'time': row.desired_time or '', 'seats_needed': int(row.seats_needed or 1),
            'price_offer': float(row.price_offer or 0), 'comment': row.comment, 'status': row.status,
            'created_at': _iso(row.created_at),
        } for row in requests]

    return HistoryResponse(city_orders=city_order_items, city_trips=city_trip_items, intercity_routes=route_items, intercity_requests=request_items)


def install_intaxi_safety_patch() -> None:
    if getattr(FastAPI, '_intaxi_safety_patch_installed', False):
        return
    previous_add_api_route = FastAPI.add_api_route

    def patched_add_api_route(self, path: str, endpoint: Callable, *args: Any, **kwargs: Any):
        methods = {str(m).upper() for m in (kwargs.get('methods') or [])}
        replacement = endpoint
        if path == '/driver/online' and 'POST' in methods:
            replacement = safe_driver_online_update
        elif path == '/city/orders/{order_id}/close' and 'POST' in methods:
            replacement = safe_city_close
        elif path == '/city/offers' and 'GET' in methods:
            replacement = safe_city_offers
        elif path == '/trip/current' and 'GET' in methods:
            replacement = safe_current_trip
        elif path == '/history/all' and 'GET' in methods:
            replacement = safe_history_all
        return previous_add_api_route(self, path, replacement, *args, **kwargs)

    FastAPI.add_api_route = patched_add_api_route
    setattr(FastAPI, '_intaxi_safety_patch_installed', True)
