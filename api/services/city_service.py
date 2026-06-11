from __future__ import annotations

from math import ceil

from sqlalchemy import select

from api.schemas import CityOrderResponse, CityTripResponse
from intaxi_bot.app.database.models import CityOrderRuntime, CityOrderV1, CityTripV1, DriverOnlineState, TariffSetting, User, Vehicle, async_session
from intaxi_bot.app.database.requests import DEFAULT_TARIFFS, haversine_km


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


def _iso(dt):
    if dt is None:
        return None
    return dt.isoformat()


def _vehicle_to_schema(vehicle: Vehicle | None):
    if not vehicle:
        return None
    return {
        'brand': vehicle.brand,
        'model': vehicle.model,
        'plate': vehicle.plate,
        'year': vehicle.year,
        'color': vehicle.color,
        'photo_tech': vehicle.photo_tech,
        'photo_license': vehicle.photo_license,
        'photo_out': vehicle.photo_out,
        'photo_in': vehicle.photo_in,
    }


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
