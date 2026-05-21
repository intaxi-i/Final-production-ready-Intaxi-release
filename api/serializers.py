from __future__ import annotations

from datetime import datetime
from math import ceil

from sqlalchemy import select

from api.deps import vehicle_to_schema
from api.schemas import (
    CityOrderResponse,
    CityTripResponse,
    IntercityOfferResponse,
)
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
from intaxi_bot.app.database.requests import haversine_km


def iso_datetime(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat()
    return str(value)


def map_provider(country: str | None) -> str:
    if country in {'uz', 'tr'}:
        return 'yandex'
    return 'google'


def map_urls(
    country: str | None,
    lat: float | None,
    lng: float | None,
    to_lat: float | None = None,
    to_lng: float | None = None,
):
    provider = map_provider(country)
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


async def city_order_to_schema(order: CityOrderV1, current_user: User | None = None) -> CityOrderResponse:
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
            created_at=iso_datetime(order.created_at),
            is_mine=bool(current_user and current_user.tg_id == order.creator_tg_id),
            active_trip_id=int(runtime.active_trip_id) if runtime and runtime.active_trip_id is not None else None,
            vehicle=vehicle_to_schema(vehicle),
            currency=runtime.currency if runtime else None,
            tariff_hint=runtime.tariff_hint if runtime else None,
        )


async def city_trip_to_schema(trip: CityTripV1) -> CityTripResponse:
    async with async_session() as session:
        passenger = await session.scalar(select(User).where(User.tg_id == trip.passenger_tg_id))
        driver = await session.scalar(select(User).where(User.tg_id == trip.driver_tg_id))
        vehicle = None
        if driver:
            vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == driver.id))
    provider, embed, action = map_urls(trip.country, trip.pickup_lat, trip.pickup_lng, trip.destination_lat, trip.destination_lng)
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
        vehicle=vehicle_to_schema(vehicle),
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


async def intercity_offer_from_route(route: IntercityRouteV1, current_user: User | None = None) -> IntercityOfferResponse:
    async with async_session() as session:
        creator = await session.scalar(select(User).where(User.tg_id == route.creator_tg_id))
        meta = await session.scalar(select(IntercityRouteMeta).where(IntercityRouteMeta.route_id == route.id))
    provider, embed, action = map_urls(route.country, meta.meeting_lat if meta else None, meta.meeting_lng if meta else None)
    return IntercityOfferResponse(
        kind='route', id=route.id, creator_tg_id=route.creator_tg_id, creator_name=creator.full_name if creator else None,
        country=route.country, from_city=route.from_city, to_city=route.to_city, date=route.departure_date, time=route.departure_time,
        seats=route.seats, price=float(route.price or 0), comment=route.comment, status=route.status, created_at=iso_datetime(route.created_at),
        is_mine=bool(current_user and current_user.tg_id == route.creator_tg_id), pickup_mode=meta.pickup_mode if meta else 'ask_driver',
        active_trip_id=route.id if route.status in {'accepted', 'in_progress'} else None,
        accepted_by_tg_id=route.accepted_by_tg_id,
        can_accept=bool(current_user and current_user.tg_id not in {route.creator_tg_id, route.accepted_by_tg_id} and route.status == 'active'),
        map_provider=provider, map_embed_url=embed, map_action_url=action,
    )


async def intercity_offer_from_request(req: IntercityRequestV1, current_user: User | None = None) -> IntercityOfferResponse:
    async with async_session() as session:
        creator = await session.scalar(select(User).where(User.tg_id == req.creator_tg_id))
    provider, embed, action = map_urls(req.country, None, None)
    return IntercityOfferResponse(
        kind='request', id=req.id, creator_tg_id=req.creator_tg_id, creator_name=creator.full_name if creator else None,
        country=req.country, from_city=req.from_city, to_city=req.to_city, date=req.desired_date, time=req.desired_time,
        seats=req.seats_needed, price=float(req.price_offer or 0), comment=req.comment, status=req.status, created_at=iso_datetime(req.created_at),
        is_mine=bool(current_user and current_user.tg_id == req.creator_tg_id), pickup_mode='ask_driver',
        active_trip_id=req.id if req.status in {'accepted', 'in_progress'} else None,
        accepted_by_tg_id=req.accepted_by_tg_id,
        can_accept=bool(current_user and current_user.tg_id not in {req.creator_tg_id, req.accepted_by_tg_id} and req.status == 'active'),
        map_provider=provider, map_embed_url=embed, map_action_url=action,
    )
