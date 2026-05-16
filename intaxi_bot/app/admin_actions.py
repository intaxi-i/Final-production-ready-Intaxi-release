from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.database.models import (
    CityOrderRuntime,
    CityOrderV1,
    CityTripV1,
    IntercityRequestV1,
    IntercityRouteV1,
    async_session,
)

FINAL_CITY_TRIP_STATUSES = {'completed', 'cancelled', 'closed', 'cancelled_by_admin'}


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def cancel_city_order(order_id: int) -> CityOrderV1 | None:
    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id).with_for_update())
        if not order:
            return None
        order.status = 'cancelled_by_admin'
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id).with_for_update())
        if runtime and runtime.active_trip_id:
            trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == runtime.active_trip_id).with_for_update())
            if trip and trip.status not in FINAL_CITY_TRIP_STATUSES:
                trip.status = 'cancelled_by_admin'
                trip.cancelled_at = _now()
                trip.updated_at = _now()
            runtime.active_trip_id = None
        await session.commit()
        await session.refresh(order)
        return order


async def cancel_intercity_route(route_id: int) -> IntercityRouteV1 | None:
    async with async_session() as session:
        row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == route_id).with_for_update())
        if not row:
            return None
        row.status = 'cancelled_by_admin'
        await session.commit()
        await session.refresh(row)
        return row


async def cancel_intercity_request(request_id: int) -> IntercityRequestV1 | None:
    async with async_session() as session:
        row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == request_id).with_for_update())
        if not row:
            return None
        row.status = 'cancelled_by_admin'
        await session.commit()
        await session.refresh(row)
        return row
