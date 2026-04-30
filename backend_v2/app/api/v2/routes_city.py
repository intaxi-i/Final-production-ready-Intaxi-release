from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.city import CityOrder, CityTrip
from app.models.driver import DriverPaymentMethod
from app.models.user import User
from app.schemas.city import (
    CityOrderCreate,
    CityOrderCreateResponse,
    CityOrderRead,
    CityTripRead,
    CityTripStatusUpdate,
    CounterofferCreate,
    CounterofferRead,
    CurrentTripResponse,
    RaisePriceRequest,
)
from app.schemas.driver import DriverPaymentMethodRead
from app.services.city_order_service import CityOrderService
from app.services.city_trip_service import CityTripService

router = APIRouter(prefix="/city", tags=["city"])


class CancelOrderRequest(BaseModel):
    reason: str | None = None


@router.post("/orders", response_model=CityOrderCreateResponse)
async def create_city_order(
    payload: CityOrderCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CityOrderCreateResponse:
    service = CityOrderService()
    order = await service.create_order(
        session,
        passenger=current_user,
        mode=payload.mode,
        country_code=payload.country_code,
        city_id=payload.city_id,
        pickup_address=payload.pickup_address,
        pickup_lat=payload.pickup_lat,
        pickup_lng=payload.pickup_lng,
        destination_address=payload.destination_address,
        destination_lat=payload.destination_lat,
        destination_lng=payload.destination_lng,
        seats=payload.seats,
        passenger_price=payload.passenger_price,
        comment=payload.comment,
    )
    await session.commit()
    await session.refresh(order)
    return CityOrderCreateResponse(
        order=CityOrderRead.model_validate(order),
        recommended_price=float(order.recommended_price) if order.recommended_price is not None else None,
        minimum_recommended_price=float(order.minimum_recommended_price) if order.minimum_recommended_price is not None else None,
        seen_by_drivers=int(order.seen_by_drivers or 0),
    )


@router.get("/orders/my", response_model=list[CityOrderRead])
async def my_city_orders(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CityOrderRead]:
    rows = (
        await session.scalars(
            select(CityOrder)
            .where(CityOrder.passenger_user_id == current_user.id)
            .order_by(CityOrder.id.desc())
            .limit(50)
        )
    ).all()
    return [CityOrderRead.model_validate(row) for row in rows]


@router.get("/orders/available", response_model=list[CityOrderRead])
async def available_city_orders(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CityOrderRead]:
    rows = (
        await session.scalars(
            select(CityOrder)
            .where(CityOrder.status == "active", CityOrder.passenger_user_id != current_user.id)
            .order_by(CityOrder.id.desc())
            .limit(100)
        )
    ).all()
    service = CityOrderService()
    result = []
    for row in rows:
        availability = await service.availability.check_driver_available_for_city_order(
            session,
            driver=current_user,
            order_country_code=row.country_code,
            order_city_id=row.city_id,
            mode=row.mode,
        )
        if availability.is_available:
            result.append(CityOrderRead.model_validate(row))
    return result


@router.post("/orders/{order_id}/raise-price", response_model=CityOrderRead)
async def raise_city_order_price(
    order_id: int,
    payload: RaisePriceRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CityOrderRead:
    order = await CityOrderService().raise_price(
        session,
        order_id=order_id,
        passenger=current_user,
        price=payload.price,
    )
    await session.commit()
    await session.refresh(order)
    return CityOrderRead.model_validate(order)


@router.post("/orders/{order_id}/cancel", response_model=CityOrderRead)
async def cancel_city_order(
    order_id: int,
    payload: CancelOrderRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CityOrderRead:
    order = await CityOrderService().cancel_order(
        session,
        order_id=order_id,
        user=current_user,
        reason=payload.reason,
    )
    await session.commit()
    await session.refresh(order)
    return CityOrderRead.model_validate(order)


@router.post("/orders/{order_id}/counteroffers", response_model=CounterofferRead)
async def create_city_counteroffer(
    order_id: int,
    payload: CounterofferCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CounterofferRead:
    offer = await CityOrderService().create_counteroffer(
        session,
        order_id=order_id,
        driver=current_user,
        price=payload.price,
    )
    await session.commit()
    await session.refresh(offer)
    return CounterofferRead.model_validate(offer)


@router.post("/orders/{order_id}/accept", response_model=CityTripRead)
async def accept_city_order(
    order_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CityTripRead:
    trip = await CityTripService().accept_order(session, order_id=order_id, driver=current_user)
    await session.commit()
    await session.refresh(trip)
    return CityTripRead.model_validate(trip)


@router.post("/counteroffers/{offer_id}/accept", response_model=CityTripRead)
async def accept_city_counteroffer(
    offer_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CityTripRead:
    trip = await CityTripService().accept_counteroffer(session, offer_id=offer_id, passenger=current_user)
    await session.commit()
    await session.refresh(trip)
    return CityTripRead.model_validate(trip)


@router.get("/trips/current", response_model=CurrentTripResponse)
async def current_city_trip(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CurrentTripResponse:
    trip = await CityTripService().get_current_trip(session, user=current_user)
    return CurrentTripResponse(item=CityTripRead.model_validate(trip) if trip else None)


@router.get("/trips/{trip_id}", response_model=CityTripRead)
async def city_trip_detail(
    trip_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CityTripRead:
    trip = await session.scalar(select(CityTrip).where(CityTrip.id == trip_id))
    if not trip or current_user.id not in {trip.passenger_user_id, trip.driver_user_id}:
        from app.core.errors import raise_domain
        raise_domain("trip_not_found", "Trip not found", 404)
    return CityTripRead.model_validate(trip)


@router.post("/trips/{trip_id}/status", response_model=CityTripRead)
async def update_city_trip_status(
    trip_id: int,
    payload: CityTripStatusUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CityTripRead:
    trip = await CityTripService().update_status(
        session,
        trip_id=trip_id,
        driver=current_user,
        target_status=payload.status,
    )
    await session.commit()
    await session.refresh(trip)
    return CityTripRead.model_validate(trip)


@router.get("/trips/{trip_id}/driver-payment-methods", response_model=list[DriverPaymentMethodRead])
async def trip_driver_payment_methods(
    trip_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DriverPaymentMethodRead]:
    trip = await session.scalar(select(CityTrip).where(CityTrip.id == trip_id))
    if not trip or trip.passenger_user_id != current_user.id:
        from app.core.errors import raise_domain
        raise_domain("payment_details_not_available", "Payment details are not available", 403)
    rows = (
        await session.scalars(
            select(DriverPaymentMethod).where(
                DriverPaymentMethod.driver_user_id == trip.driver_user_id,
                DriverPaymentMethod.is_active == True,
            )
        )
    ).all()
    return [DriverPaymentMethodRead.model_validate(row) for row in rows]
