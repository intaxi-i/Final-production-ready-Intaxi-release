from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import raise_domain
from app.domain.ride_statuses import TRIP_TO_ORDER_STATUS, can_transition_city_trip
from app.models.city import CityCounteroffer, CityOrder, CityTrip
from app.models.driver import DriverOnlineState, Vehicle
from app.models.user import User
from app.services.driver_availability_service import DriverAvailabilityService, LIVE_TRIP_STATUSES


class CityTripService:
    def __init__(self, availability: DriverAvailabilityService | None = None) -> None:
        self.availability = availability or DriverAvailabilityService()

    async def accept_order(
        self,
        session: AsyncSession,
        *,
        order_id: int,
        driver: User,
        final_price: float | None = None,
    ) -> CityTrip:
        order = await session.scalar(select(CityOrder).where(CityOrder.id == order_id))
        if not order:
            raise_domain("order_not_found", "Order not found", 404)
        if order.status != "active":
            raise_domain("order_not_active", "Order is not active", 409)
        if order.passenger_user_id == driver.id:
            raise_domain("cannot_accept_own_order", "Driver cannot accept own order", 403)
        availability = await self.availability.check_driver_available_for_city_order(
            session,
            driver=driver,
            order_country_code=order.country_code,
            order_city_id=order.city_id,
            mode=order.mode,
        )
        if not availability.is_available:
            raise_domain("driver_not_available", "Driver is not available", 403, reason=availability.reason)

        vehicle = await session.scalar(
            select(Vehicle).where(
                Vehicle.driver_user_id == driver.id,
                Vehicle.status == "approved",
            ).order_by(Vehicle.id.desc())
        )
        online = await session.scalar(
            select(DriverOnlineState).where(DriverOnlineState.driver_user_id == driver.id)
        )
        trip = CityTrip(
            mode=order.mode,
            order_id=order.id,
            passenger_user_id=order.passenger_user_id,
            driver_user_id=driver.id,
            vehicle_id=vehicle.id if vehicle else None,
            final_price=float(final_price if final_price is not None else order.passenger_price),
            currency=order.currency,
            status="accepted",
            pickup_address=order.pickup_address,
            pickup_lat=order.pickup_lat,
            pickup_lng=order.pickup_lng,
            destination_address=order.destination_address,
            destination_lat=order.destination_lat,
            destination_lng=order.destination_lng,
            driver_lat=online.lat if online else None,
            driver_lng=online.lng if online else None,
            passenger_lat=order.pickup_lat,
            passenger_lng=order.pickup_lng,
            accepted_at=datetime.now(timezone.utc),
        )
        session.add(trip)
        await session.flush()

        order.status = "accepted"
        order.accepted_trip_id = trip.id
        if online:
            online.is_busy = True
        await session.flush()
        return trip

    async def accept_counteroffer(
        self,
        session: AsyncSession,
        *,
        offer_id: int,
        passenger: User,
    ) -> CityTrip:
        offer = await session.scalar(select(CityCounteroffer).where(CityCounteroffer.id == offer_id))
        if not offer:
            raise_domain("offer_not_found", "Counteroffer not found", 404)
        if offer.status != "pending":
            raise_domain("offer_not_pending", "Counteroffer is not pending", 409)
        order = await session.scalar(select(CityOrder).where(CityOrder.id == offer.order_id))
        if not order:
            raise_domain("order_not_found", "Order not found", 404)
        if order.passenger_user_id != passenger.id:
            raise_domain("forbidden", "Only order passenger can accept counteroffer", 403)
        driver = await session.scalar(select(User).where(User.id == offer.driver_user_id))
        if not driver:
            raise_domain("driver_not_found", "Driver not found", 404)
        trip = await self.accept_order(
            session,
            order_id=order.id,
            driver=driver,
            final_price=float(offer.price),
        )
        offer.status = "accepted"
        other_offers = (
            await session.scalars(
                select(CityCounteroffer).where(
                    CityCounteroffer.order_id == order.id,
                    CityCounteroffer.id != offer.id,
                    CityCounteroffer.status == "pending",
                )
            )
        ).all()
        for other in other_offers:
            other.status = "rejected"
        await session.flush()
        return trip

    async def get_current_trip(self, session: AsyncSession, *, user: User) -> CityTrip | None:
        return await session.scalar(
            select(CityTrip)
            .where(
                or_(CityTrip.passenger_user_id == user.id, CityTrip.driver_user_id == user.id),
                CityTrip.status.in_(LIVE_TRIP_STATUSES),
            )
            .order_by(CityTrip.id.desc())
        )

    async def update_status(
        self,
        session: AsyncSession,
        *,
        trip_id: int,
        driver: User,
        target_status: str,
    ) -> CityTrip:
        trip = await session.scalar(select(CityTrip).where(CityTrip.id == trip_id))
        if not trip:
            raise_domain("trip_not_found", "Trip not found", 404)
        if trip.driver_user_id != driver.id:
            raise_domain("only_driver_can_update_trip", "Only assigned driver can update trip", 403)
        if not can_transition_city_trip(str(trip.status), target_status):
            raise_domain(
                "invalid_status_transition",
                "Invalid status transition",
                409,
                current=trip.status,
                target=target_status,
            )
        now = datetime.now(timezone.utc)
        trip.status = target_status
        if target_status == "in_progress" and trip.started_at is None:
            trip.started_at = now
        if target_status == "completed":
            trip.completed_at = now
        if target_status == "cancelled":
            trip.cancelled_at = now
        order = await session.scalar(select(CityOrder).where(CityOrder.id == trip.order_id))
        if order:
            order.status = TRIP_TO_ORDER_STATUS.get(target_status, order.status)
        if target_status in {"completed", "cancelled"}:
            online = await session.scalar(
                select(DriverOnlineState).where(DriverOnlineState.driver_user_id == trip.driver_user_id)
            )
            if online:
                online.is_busy = False
        await session.flush()
        return trip
