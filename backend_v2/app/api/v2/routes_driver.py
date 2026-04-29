from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.errors import raise_domain
from app.models.driver import DriverOnlineState, DriverPaymentMethod, DriverProfile, Vehicle
from app.models.user import User
from app.schemas.driver import (
    DriverLocationUpdate,
    DriverOnlineRead,
    DriverOnlineUpdate,
    DriverPaymentMethodCreate,
    DriverPaymentMethodRead,
)

router = APIRouter(prefix="/driver", tags=["driver"])


def _mask_card(card_number: str | None) -> str | None:
    if not card_number:
        return None
    digits = ''.join(ch for ch in card_number if ch.isdigit())
    if len(digits) < 8:
        return '****'
    return f"{digits[:4]}********{digits[-4:]}"


@router.get("/online", response_model=DriverOnlineRead)
async def get_driver_online(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DriverOnlineRead:
    row = await session.scalar(
        select(DriverOnlineState).where(DriverOnlineState.driver_user_id == current_user.id)
    )
    if not row:
        return DriverOnlineRead(is_online=False, is_busy=False)
    return DriverOnlineRead(
        is_online=bool(row.is_online),
        is_busy=bool(row.is_busy),
        country_code=row.country_code,
        city_id=row.city_id,
        lat=float(row.lat) if row.lat is not None else None,
        lng=float(row.lng) if row.lng is not None else None,
    )


@router.post("/online", response_model=DriverOnlineRead)
async def set_driver_online(
    payload: DriverOnlineUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DriverOnlineRead:
    if current_user.is_blocked:
        raise_domain("driver_blocked", "Blocked driver cannot go online", 403)
    profile = await session.scalar(select(DriverProfile).where(DriverProfile.user_id == current_user.id))
    if not profile or profile.status != "approved":
        raise_domain("driver_not_approved", "Only approved drivers can go online", 403)
    row = await session.scalar(
        select(DriverOnlineState).where(DriverOnlineState.driver_user_id == current_user.id)
    )
    if not row:
        row = DriverOnlineState(driver_user_id=current_user.id)
        session.add(row)
    row.is_online = bool(payload.is_online)
    row.country_code = payload.country_code or current_user.country_code or profile.country_code
    row.city_id = payload.city_id or current_user.city_id or profile.city_id
    row.updated_at = datetime.now(timezone.utc)
    current_user.active_role = "driver"
    await session.commit()
    await session.refresh(row)
    return DriverOnlineRead(
        is_online=bool(row.is_online),
        is_busy=bool(row.is_busy),
        country_code=row.country_code,
        city_id=row.city_id,
        lat=float(row.lat) if row.lat is not None else None,
        lng=float(row.lng) if row.lng is not None else None,
    )


@router.post("/location", response_model=dict)
async def update_driver_location(
    payload: DriverLocationUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    profile = await session.scalar(select(DriverProfile).where(DriverProfile.user_id == current_user.id))
    if not profile or profile.status != "approved":
        raise_domain("driver_not_approved", "Only approved drivers can update location", 403)
    row = await session.scalar(
        select(DriverOnlineState).where(DriverOnlineState.driver_user_id == current_user.id)
    )
    if not row:
        row = DriverOnlineState(driver_user_id=current_user.id)
        session.add(row)
    row.lat = payload.lat
    row.lng = payload.lng
    row.is_online = True
    row.country_code = current_user.country_code or profile.country_code
    row.city_id = current_user.city_id or profile.city_id
    row.last_location_at = datetime.now(timezone.utc)
    row.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"status": "ok"}


@router.post("/payment-methods", response_model=DriverPaymentMethodRead)
async def create_driver_payment_method(
    payload: DriverPaymentMethodCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DriverPaymentMethodRead:
    profile = await session.scalar(select(DriverProfile).where(DriverProfile.user_id == current_user.id))
    if not profile or profile.status != "approved":
        raise_domain("driver_not_approved", "Only approved drivers can add payment methods", 403)
    row = DriverPaymentMethod(
        driver_user_id=current_user.id,
        country_code=payload.country_code.lower(),
        method_type=payload.method_type,
        card_number_masked=_mask_card(payload.card_number),
        card_number_encrypted=payload.card_number,
        card_holder_name=payload.card_holder_name,
        bank_name=payload.bank_name,
        is_active=True,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return DriverPaymentMethodRead.model_validate(row)


@router.get("/payment-methods", response_model=list[DriverPaymentMethodRead])
async def list_driver_payment_methods(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DriverPaymentMethodRead]:
    rows = (
        await session.scalars(
            select(DriverPaymentMethod)
            .where(DriverPaymentMethod.driver_user_id == current_user.id)
            .order_by(DriverPaymentMethod.id.desc())
        )
    ).all()
    return [DriverPaymentMethodRead.model_validate(row) for row in rows]
