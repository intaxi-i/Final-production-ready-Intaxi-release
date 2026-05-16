from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.database.models import CityOrderRuntime, CityOrderV1, CityTripV1, async_session

FINAL_CITY_TRIP_STATUSES = {'completed', 'cancelled', 'closed', 'cancelled_by_admin'}


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def close_city_order_for_user(order_id: int, tg_id: int) -> CityOrderV1 | None:
    async with async_session() as session:
        order = await session.scalar(
            select(CityOrderV1).where(CityOrderV1.id == order_id, CityOrderV1.creator_tg_id == tg_id).with_for_update()
        )
        if not order:
            return None
        order.status = 'closed'
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id).with_for_update())
        if runtime and runtime.active_trip_id:
            trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == runtime.active_trip_id).with_for_update())
            if trip and trip.status not in FINAL_CITY_TRIP_STATUSES:
                trip.status = 'cancelled'
                trip.cancelled_at = _now()
                trip.updated_at = _now()
            runtime.active_trip_id = None
        await session.commit()
        await session.refresh(order)
        return order
