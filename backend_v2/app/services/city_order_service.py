from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import raise_domain
from app.models.city import CityCounteroffer, CityOrder, CityTrip
from app.models.country import Country
from app.models.driver import DriverOnlineState
from app.models.user import User
from app.services.driver_availability_service import DriverAvailabilityService
from app.services.pricing_service import PricingService


class CityOrderService:
    def __init__(
        self,
        pricing: PricingService | None = None,
        availability: DriverAvailabilityService | None = None,
    ) -> None:
        self.pricing = pricing or PricingService()
        self.availability = availability or DriverAvailabilityService()

    async def create_order(
        self,
        session: AsyncSession,
        *,
        passenger: User,
        mode: str,
        country_code: str,
        city_id: int | None,
        pickup_address: str,
        pickup_lat: float | None,
        pickup_lng: float | None,
        destination_address: str,
        destination_lat: float | None,
        destination_lng: float | None,
        seats: int,
        passenger_price: float,
        comment: str | None = None,
    ) -> CityOrder:
        if passenger.is_blocked:
            raise_domain("user_blocked", "Blocked user cannot create order", 403)
        if passenger.active_role not in (None, "passenger"):
            raise_domain("passenger_role_required", "Switch to passenger role first", 403)
        if mode == "women" and (passenger.profile_gender != "woman" or not passenger.is_adult_confirmed):
            raise_domain("women_mode_not_allowed", "User is not eligible for women mode", 403)
        if passenger_price <= 0:
            raise_domain("invalid_price", "Passenger price must be positive")

        country = await session.scalar(select(Country).where(Country.code == country_code.lower()))
        currency = country.currency if country else "USD"
        price_per_km = 2500.0 if currency == "UZS" else 1.0
        minimum_fare = 10000.0 if currency == "UZS" else 1.0
        estimate = self.pricing.estimate_city_price(
            currency=currency,
            price_per_km=price_per_km,
            minimum_fare=minimum_fare,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            destination_lat=destination_lat,
            destination_lng=destination_lng,
        )
        drivers = await self.availability.list_matching_city_drivers(
            session,
            country_code=country_code.lower(),
            city_id=city_id,
            mode=mode,
        )
        order = CityOrder(
            mode=mode,
            passenger_user_id=passenger.id,
            country_code=country_code.lower(),
            city_id=city_id,
            pickup_address=pickup_address,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            destination_address=destination_address,
            destination_lat=destination_lat,
            destination_lng=destination_lng,
            seats=max(1, int(seats or 1)),
            passenger_price=float(passenger_price),
            recommended_price=estimate.recommended_price,
            minimum_recommended_price=estimate.minimum_recommended_price,
            currency=estimate.currency,
            estimated_distance_km=estimate.distance_km,
            estimated_duration_min=estimate.duration_min,
            status="active",
            seen_by_drivers=len(drivers),
        )
        session.add(order)
        await session.flush()
        return order

    async def raise_price(
        self,
        session: AsyncSession,
        *,
        order_id: int,
        passenger: User,
        price: float,
    ) -> CityOrder:
        order = await session.scalar(select(CityOrder).where(CityOrder.id == order_id))
        if not order:
            raise_domain("order_not_found", "Order not found", 404)
        if order.passenger_user_id != passenger.id:
            raise_domain("forbidden", "Only order owner can raise price", 403)
        if order.status != "active":
            raise_domain("order_not_active", "Only active order price can be changed", 409)
        if price <= order.passenger_price:
            raise_domain("invalid_price", "New price must be higher than current price")
        order.passenger_price = float(price)
        await session.flush()
        return order

    async def create_counteroffer(
        self,
        session: AsyncSession,
        *,
        order_id: int,
        driver: User,
        price: float,
    ) -> CityCounteroffer:
        order = await session.scalar(select(CityOrder).where(CityOrder.id == order_id))
        if not order:
            raise_domain("order_not_found", "Order not found", 404)
        if order.status != "active":
            raise_domain("order_not_active", "Order is not active", 409)
        availability = await self.availability.check_driver_available_for_city_order(
            session,
            driver=driver,
            order_country_code=order.country_code,
            order_city_id=order.city_id,
            mode=order.mode,
        )
        if not availability.is_available:
            raise_domain("driver_not_available", "Driver is not available", 403, reason=availability.reason)
        if price <= 0:
            raise_domain("invalid_price", "Counteroffer price must be positive")
        existing = await session.scalar(
            select(CityCounteroffer).where(
                CityCounteroffer.order_id == order.id,
                CityCounteroffer.driver_user_id == driver.id,
                CityCounteroffer.status == "pending",
            )
        )
        if existing:
            existing.price = float(price)
            await session.flush()
            return existing
        offer = CityCounteroffer(
            order_id=order.id,
            driver_user_id=driver.id,
            price=float(price),
            currency=order.currency,
            status="pending",
        )
        session.add(offer)
        await session.flush()
        return offer

    async def cancel_order(
        self,
        session: AsyncSession,
        *,
        order_id: int,
        user: User,
        reason: str | None = None,
    ) -> CityOrder:
        order = await session.scalar(select(CityOrder).where(CityOrder.id == order_id))
        if not order:
            raise_domain("order_not_found", "Order not found", 404)
        if order.passenger_user_id != user.id:
            raise_domain("forbidden", "Only order owner can cancel order", 403)
        if order.status not in {"active", "accepted"}:
            raise_domain("order_cannot_cancel", "Order cannot be cancelled in current status", 409)
        order.status = "cancelled"
        order.cancel_reason = reason
        if order.accepted_trip_id:
            trip = await session.scalar(select(CityTrip).where(CityTrip.id == order.accepted_trip_id))
            if trip and trip.status not in {"completed", "cancelled"}:
                trip.status = "cancelled"
                state = await session.scalar(
                    select(DriverOnlineState).where(DriverOnlineState.driver_user_id == trip.driver_user_id)
                )
                if state:
                    state.is_busy = False
        await session.flush()
        return order
