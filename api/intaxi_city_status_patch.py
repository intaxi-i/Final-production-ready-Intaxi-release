from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, HTTPException
from sqlalchemy import select

from api.auth import get_current_user
from api.schemas import CityTripEnvelope, CityTripResponse, CityTripStatusUpdateRequest, VehicleInfo
from intaxi_bot.app.database.models import CityOrderRuntime, CityOrderV1, CityTripV1, User, Vehicle, async_session
from api.services.lifecycle import ensure_city_transition_allowed, ensure_supported_city_status, now_utc

def _map_provider(country: str | None) -> str:
    return 'yandex' if country in {'uz', 'tr'} else 'google'


def _map_urls(country: str | None, lat: float | None, lng: float | None, to_lat: float | None = None, to_lng: float | None = None) -> tuple[str, str | None, str | None]:
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


def _vehicle_schema(vehicle: Vehicle | None) -> VehicleInfo | None:
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


async def _trip_response(session, trip: CityTripV1) -> CityTripResponse:
    passenger = await session.scalar(select(User).where(User.tg_id == trip.passenger_tg_id))
    driver = await session.scalar(select(User).where(User.tg_id == trip.driver_tg_id))
    vehicle = None
    if driver:
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == driver.id))
    provider, embed, action = _map_urls(trip.country, trip.pickup_lat, trip.pickup_lng, trip.destination_lat, trip.destination_lng)
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
        vehicle=_vehicle_schema(vehicle),
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
    )


async def strict_city_trip_status(trip_id: int, payload: CityTripStatusUpdateRequest, current_user: User = Depends(get_current_user)) -> CityTripEnvelope:
    new_status = payload.status
    ensure_supported_city_status(new_status)

    async with async_session() as session:
        trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == trip_id).with_for_update())
        if not trip:
            raise HTTPException(status_code=404, detail='Trip not found')
        is_driver = current_user.tg_id == trip.driver_tg_id
        is_passenger = current_user.tg_id == trip.passenger_tg_id
        ensure_city_transition_allowed(trip.status, new_status, is_driver=is_driver, is_passenger=is_passenger)
        if trip.status == new_status:
            return CityTripEnvelope(item=await _trip_response(session, trip))

        trip.status = new_status
        trip.updated_at = now_utc()
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == trip.order_id).with_for_update())
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == trip.order_id).with_for_update())

        if new_status == 'completed':
            trip.completed_at = now_utc()
            if order:
                order.status = 'completed'
            if runtime:
                runtime.active_trip_id = None
        elif new_status in {'cancelled', 'closed', 'cancelled_by_admin'}:
            trip.cancelled_at = now_utc()
            if order:
                order.status = 'cancelled'
            if runtime:
                runtime.active_trip_id = None

        await session.commit()
        await session.refresh(trip)
        return CityTripEnvelope(item=await _trip_response(session, trip))
