from __future__ import annotations

from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import raise_domain
from app.models.driver import DriverProfile, Vehicle
from app.models.intercity import IntercityRequest, IntercityRoute, IntercityTrip
from app.models.user import User


class IntercityService:
    async def create_request(
        self,
        session: AsyncSession,
        *,
        passenger: User,
        mode: str,
        country_code: str,
        from_city_id: int | None,
        to_city_id: int | None,
        from_text: str,
        to_text: str,
        ride_date: date_type | None,
        ride_time: str | None,
        seats: int,
        passenger_price: float,
        currency: str,
        comment: str | None = None,
    ) -> IntercityRequest:
        if passenger.is_blocked:
            raise_domain("user_blocked", "Blocked user cannot create intercity request", 403)
        if mode == "women" and (passenger.profile_gender != "woman" or not passenger.is_adult_confirmed):
            raise_domain("women_mode_not_allowed", "User is not eligible for women mode", 403)
        if passenger_price <= 0:
            raise_domain("invalid_price", "Passenger price must be positive")
        row = IntercityRequest(
            mode=mode,
            passenger_user_id=passenger.id,
            country_code=country_code.lower(),
            from_city_id=from_city_id,
            to_city_id=to_city_id,
            from_text=from_text,
            to_text=to_text,
            date=ride_date,
            time=ride_time,
            seats=max(1, int(seats or 1)),
            passenger_price=float(passenger_price),
            currency=currency,
            status="active",
            comment=comment,
        )
        session.add(row)
        await session.flush()
        return row

    async def create_route(
        self,
        session: AsyncSession,
        *,
        driver: User,
        mode: str,
        country_code: str,
        from_city_id: int | None,
        to_city_id: int | None,
        from_text: str,
        to_text: str,
        ride_date: date_type | None,
        ride_time: str | None,
        seats_available: int,
        price_per_seat: float,
        currency: str,
        pickup_mode: str = "ask_driver",
        comment: str | None = None,
    ) -> IntercityRoute:
        profile = await session.scalar(select(DriverProfile).where(DriverProfile.user_id == driver.id))
        if driver.is_blocked or not profile or profile.status != "approved":
            raise_domain("driver_not_approved", "Only approved drivers can create intercity route", 403)
        if mode == "women":
            if driver.profile_gender != "woman" or not driver.is_adult_confirmed:
                raise_domain("women_mode_not_allowed", "Driver is not eligible for women mode", 403)
            if not profile.is_woman_driver_verified or profile.woman_driver_status != "approved":
                raise_domain("woman_driver_not_approved", "Woman driver mode is not approved", 403)
        if price_per_seat <= 0:
            raise_domain("invalid_price", "Route price must be positive")
        row = IntercityRoute(
            mode=mode,
            driver_user_id=driver.id,
            country_code=country_code.lower(),
            from_city_id=from_city_id,
            to_city_id=to_city_id,
            from_text=from_text,
            to_text=to_text,
            date=ride_date,
            time=ride_time,
            seats_available=max(1, int(seats_available or 1)),
            price_per_seat=float(price_per_seat),
            currency=currency,
            pickup_mode=pickup_mode,
            status="active",
            comment=comment,
        )
        session.add(row)
        await session.flush()
        return row

    async def accept_request(self, session: AsyncSession, *, request_id: int, driver: User) -> IntercityTrip:
        req = await session.scalar(select(IntercityRequest).where(IntercityRequest.id == request_id))
        if not req:
            raise_domain("intercity_request_not_found", "Intercity request not found", 404)
        if req.status != "active":
            raise_domain("intercity_request_not_active", "Intercity request is not active", 409)
        if req.passenger_user_id == driver.id:
            raise_domain("cannot_accept_own_request", "Driver cannot accept own request", 403)
        profile = await session.scalar(select(DriverProfile).where(DriverProfile.user_id == driver.id))
        if not profile or profile.status != "approved":
            raise_domain("driver_not_approved", "Only approved drivers can accept request", 403)
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.driver_user_id == driver.id, Vehicle.status == "approved").order_by(Vehicle.id.desc()))
        trip = IntercityTrip(
            mode=req.mode,
            source_type="request",
            source_id=req.id,
            passenger_user_id=req.passenger_user_id,
            driver_user_id=driver.id,
            vehicle_id=vehicle.id if vehicle else None,
            final_price=float(req.passenger_price),
            currency=req.currency,
            status="accepted",
        )
        session.add(trip)
        await session.flush()
        req.status = "accepted"
        await session.flush()
        return trip

    async def accept_route(self, session: AsyncSession, *, route_id: int, passenger: User) -> IntercityTrip:
        route = await session.scalar(select(IntercityRoute).where(IntercityRoute.id == route_id))
        if not route:
            raise_domain("intercity_route_not_found", "Intercity route not found", 404)
        if route.status != "active":
            raise_domain("intercity_route_not_active", "Intercity route is not active", 409)
        if route.driver_user_id == passenger.id:
            raise_domain("cannot_accept_own_route", "Passenger cannot accept own route", 403)
        trip = IntercityTrip(
            mode=route.mode,
            source_type="route",
            source_id=route.id,
            passenger_user_id=passenger.id,
            driver_user_id=route.driver_user_id,
            vehicle_id=None,
            final_price=float(route.price_per_seat),
            currency=route.currency,
            status="accepted",
        )
        session.add(trip)
        await session.flush()
        route.status = "accepted"
        await session.flush()
        return trip
