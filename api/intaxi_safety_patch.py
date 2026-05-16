from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import or_, select

from api.auth import get_current_user
from api.order_actions import close_city_order_for_user
from api.schemas import CurrentTripResponse
from intaxi_bot.app.database.models import (
    CityOrderRuntime,
    CityOrderV1,
    CityTripV1,
    IntercityRequestV1,
    IntercityRouteMeta,
    IntercityRouteV1,
    User,
    Vehicle,
    async_session,
)

LIVE_CITY_STATUSES = {'accepted', 'driver_on_way', 'driver_arrived', 'in_progress'}
LIVE_INTERCITY_STATUSES = {'active', 'accepted', 'in_progress'}


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


async def safe_city_close(order_id: int, current_user: User = Depends(get_current_user)) -> dict:
    row = await close_city_order_for_user(order_id, current_user.tg_id)
    if not row:
        raise HTTPException(status_code=404, detail='Order not found')
    return {'id': row.id, 'status': row.status}


async def safe_current_trip(current_user: User = Depends(get_current_user)) -> CurrentTripResponse:
    async with async_session() as session:
        trip = await session.scalar(
            select(CityTripV1)
            .where(
                or_(CityTripV1.passenger_tg_id == current_user.tg_id, CityTripV1.driver_tg_id == current_user.tg_id),
                CityTripV1.status.in_(list(LIVE_CITY_STATUSES)),
            )
            .order_by(CityTripV1.id.desc())
        )
        if trip:
            passenger = await session.scalar(select(User).where(User.tg_id == trip.passenger_tg_id))
            driver = await session.scalar(select(User).where(User.tg_id == trip.driver_tg_id))
            vehicle = None
            if driver:
                vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == driver.id))
            provider, embed, action = _map_urls(trip.country, trip.pickup_lat, trip.pickup_lng, trip.destination_lat, trip.destination_lng)
            return CurrentTripResponse(item={
                'id': trip.id,
                'order_id': trip.order_id,
                'trip_type': 'city_trip',
                'status': trip.status,
                'price': float(trip.price or 0),
                'country': trip.country,
                'city': trip.city,
                'from_address': trip.from_address,
                'to_address': trip.to_address,
                'seats': trip.seats,
                'comment': trip.comment,
                'passenger_tg_id': trip.passenger_tg_id,
                'driver_tg_id': trip.driver_tg_id,
                'passenger_name': passenger.full_name if passenger else None,
                'passenger_username': passenger.username if passenger else None,
                'driver_name': driver.full_name if driver else None,
                'driver_username': driver.username if driver else None,
                'driver_rating': float(driver.rating or 0) if driver else None,
                'vehicle': {
                    'brand': vehicle.brand,
                    'model': vehicle.model,
                    'plate': vehicle.plate,
                    'color': vehicle.color,
                    'capacity': vehicle.capacity,
                    'vehicle_class': vehicle.vehicle_class,
                } if vehicle else None,
                'pickup_lat': trip.pickup_lat,
                'pickup_lng': trip.pickup_lng,
                'destination_lat': trip.destination_lat,
                'destination_lng': trip.destination_lng,
                'driver_lat': trip.driver_lat,
                'driver_lng': trip.driver_lng,
                'passenger_lat': trip.passenger_lat,
                'passenger_lng': trip.passenger_lng,
                'map_provider': provider,
                'map_embed_url': embed,
                'map_action_url': action,
            })

        order = await session.scalar(
            select(CityOrderV1)
            .where(CityOrderV1.creator_tg_id == current_user.tg_id, CityOrderV1.status == 'active', CityOrderV1.role == 'passenger')
            .order_by(CityOrderV1.id.desc())
        )
        if order:
            runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
            return CurrentTripResponse(item={
                'id': order.id,
                'trip_type': 'city_order',
                'status': order.status,
                'price': float(order.price or 0),
                'country': order.country,
                'city': order.city,
                'from_address': order.from_address,
                'to_address': order.to_address,
                'seats': order.seats,
                'comment': order.comment,
                'creator_tg_id': order.creator_tg_id,
                'is_mine': True,
                'active_trip_id': int(runtime.active_trip_id) if runtime and runtime.active_trip_id is not None else None,
                'currency': runtime.currency if runtime else None,
                'tariff_hint': runtime.tariff_hint if runtime else None,
            })

        route = await session.scalar(
            select(IntercityRouteV1)
            .where(
                or_(IntercityRouteV1.creator_tg_id == current_user.tg_id, IntercityRouteV1.accepted_by_tg_id == current_user.tg_id),
                IntercityRouteV1.status.in_(list(LIVE_INTERCITY_STATUSES)),
            )
            .order_by(IntercityRouteV1.id.desc())
        )
        if route:
            meta = await session.scalar(select(IntercityRouteMeta).where(IntercityRouteMeta.route_id == route.id))
            provider, embed, action = _map_urls(route.country, meta.meeting_lat if meta else None, meta.meeting_lng if meta else None)
            return CurrentTripResponse(item={
                'id': route.id,
                'trip_type': 'intercity_route',
                'status': route.status,
                'price': float(route.price or 0),
                'country': route.country,
                'from_city': route.from_city,
                'to_city': route.to_city,
                'comment': route.comment,
                'pickup_mode': meta.pickup_mode if meta else 'ask_driver',
                'map_provider': provider,
                'map_embed_url': embed,
                'map_action_url': action,
                'date': route.departure_date,
                'time': route.departure_time,
                'seats': route.seats,
                'accepted_by_tg_id': route.accepted_by_tg_id,
                'creator_tg_id': route.creator_tg_id,
                'is_mine': current_user.tg_id == route.creator_tg_id,
            })

        req = await session.scalar(
            select(IntercityRequestV1)
            .where(
                or_(IntercityRequestV1.creator_tg_id == current_user.tg_id, IntercityRequestV1.accepted_by_tg_id == current_user.tg_id),
                IntercityRequestV1.status.in_(list(LIVE_INTERCITY_STATUSES)),
            )
            .order_by(IntercityRequestV1.id.desc())
        )
        if req:
            provider, embed, action = _map_urls(req.country, None, None)
            return CurrentTripResponse(item={
                'id': req.id,
                'trip_type': 'intercity_request',
                'status': req.status,
                'price': float(req.price_offer or 0),
                'country': req.country,
                'from_city': req.from_city,
                'to_city': req.to_city,
                'comment': req.comment,
                'map_provider': provider,
                'map_embed_url': embed,
                'map_action_url': action,
                'date': req.desired_date,
                'time': req.desired_time,
                'seats': req.seats_needed,
                'accepted_by_tg_id': req.accepted_by_tg_id,
                'creator_tg_id': req.creator_tg_id,
                'is_mine': current_user.tg_id == req.creator_tg_id,
            })
    return CurrentTripResponse(item=None)


def install_intaxi_safety_patch() -> None:
    if getattr(FastAPI, '_intaxi_safety_patch_installed', False):
        return
    previous_add_api_route = FastAPI.add_api_route

    def patched_add_api_route(self, path: str, endpoint: Callable, *args: Any, **kwargs: Any):
        methods = {str(m).upper() for m in (kwargs.get('methods') or [])}
        replacement = endpoint
        if path == '/city/orders/{order_id}/close' and 'POST' in methods:
            replacement = safe_city_close
        elif path == '/trip/current' and 'GET' in methods:
            replacement = safe_current_trip
        return previous_add_api_route(self, path, replacement, *args, **kwargs)

    FastAPI.add_api_route = patched_add_api_route
    setattr(FastAPI, '_intaxi_safety_patch_installed', True)
