from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import CityTrip
from app.models.driver import DriverOnlineState, DriverProfile
from app.models.user import User

LIVE_TRIP_STATUSES = {"accepted", "driver_on_way", "driver_arrived", "in_progress"}


@dataclass(frozen=True, slots=True)
class DriverAvailability:
    is_available: bool
    reason: str | None = None


class DriverAvailabilityService:
    async def has_live_city_trip(self, session: AsyncSession, driver_user_id: int) -> bool:
        trip = await session.scalar(
            select(CityTrip)
            .where(
                CityTrip.driver_user_id == driver_user_id,
                CityTrip.status.in_(LIVE_TRIP_STATUSES),
            )
            .order_by(CityTrip.id.desc())
        )
        return trip is not None

    async def check_driver_available_for_city_order(
        self,
        session: AsyncSession,
        *,
        driver: User,
        order_country_code: str,
        order_city_id: int | None,
        mode: str,
    ) -> DriverAvailability:
        if driver.is_blocked:
            return DriverAvailability(False, "driver_blocked")
        if driver.active_role != "driver":
            return DriverAvailability(False, "not_driver_role")
        profile = await session.scalar(select(DriverProfile).where(DriverProfile.user_id == driver.id))
        if not profile or profile.status != "approved":
            return DriverAvailability(False, "driver_not_approved")
        if mode == "women":
            if driver.profile_gender != "woman" or not driver.is_adult_confirmed:
                return DriverAvailability(False, "driver_not_eligible_for_women_mode")
            if not profile.is_woman_driver_verified or profile.woman_driver_status != "approved":
                return DriverAvailability(False, "woman_driver_not_approved")
        online = await session.scalar(
            select(DriverOnlineState).where(DriverOnlineState.driver_user_id == driver.id)
        )
        if not online or not online.is_online:
            return DriverAvailability(False, "driver_offline")
        if online.is_busy:
            return DriverAvailability(False, "driver_busy")
        if online.country_code and online.country_code.lower() != order_country_code.lower():
            return DriverAvailability(False, "country_mismatch")
        if order_city_id is not None and online.city_id is not None and online.city_id != order_city_id:
            return DriverAvailability(False, "city_mismatch")
        if await self.has_live_city_trip(session, driver.id):
            return DriverAvailability(False, "driver_has_live_trip")
        return DriverAvailability(True)

    async def list_matching_city_drivers(
        self,
        session: AsyncSession,
        *,
        country_code: str,
        city_id: int | None,
        mode: str,
        limit: int = 50,
    ) -> list[User]:
        query = (
            select(User)
            .join(DriverOnlineState, DriverOnlineState.driver_user_id == User.id)
            .where(
                User.is_blocked == False,
                User.active_role == "driver",
                DriverOnlineState.is_online == True,
                DriverOnlineState.is_busy == False,
                or_(DriverOnlineState.country_code == None, DriverOnlineState.country_code == country_code),
            )
            .limit(limit * 3)
        )
        if city_id is not None:
            query = query.where(or_(DriverOnlineState.city_id == None, DriverOnlineState.city_id == city_id))
        rows = (await session.scalars(query)).all()
        result: list[User] = []
        for driver in rows:
            availability = await self.check_driver_available_for_city_order(
                session,
                driver=driver,
                order_country_code=country_code,
                order_city_id=city_id,
                mode=mode,
            )
            if availability.is_available:
                result.append(driver)
            if len(result) >= limit:
                break
        return result
