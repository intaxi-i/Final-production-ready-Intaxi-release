from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.core.errors import raise_domain
from app.models.commission import CommissionRule
from app.models.driver import DriverProfile
from app.models.money import PaymentTopupRequest
from app.models.user import User
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=dict)
async def admin_dashboard(session: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)) -> dict:
    pending_drivers = len((await session.scalars(select(DriverProfile).where(DriverProfile.status == "pending"))).all())
    pending_topups = len((await session.scalars(select(PaymentTopupRequest).where(PaymentTopupRequest.status == "pending"))).all())
    return {"pending_drivers": pending_drivers, "pending_topups": pending_topups}


@router.get("/drivers/pending", response_model=list[dict])
async def pending_drivers(session: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)) -> list[dict]:
    rows = (await session.scalars(select(DriverProfile).where(DriverProfile.status == "pending"))).all()
    return [{"id": row.id, "user_id": row.user_id, "country_code": row.country_code, "city_id": row.city_id} for row in rows]


@router.post("/drivers/{driver_profile_id}/approve", response_model=dict)
async def approve_driver(driver_profile_id: int, session: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)) -> dict:
    row = await session.scalar(select(DriverProfile).where(DriverProfile.id == driver_profile_id))
    if not row:
        raise_domain("driver_profile_not_found", "Driver profile not found", 404)
    row.status = "approved"
    row.reviewed_by_admin_id = admin.id
    await session.commit()
    return {"id": row.id, "status": row.status}


@router.post("/payments/{payment_id}/approve", response_model=dict)
async def approve_payment(payment_id: int, session: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)) -> dict:
    row = await WalletService().approve_topup(session, topup_id=payment_id, admin=admin)
    await session.commit()
    return {"id": row.id, "status": row.status}


@router.get("/commission-rules", response_model=list[dict])
async def list_commission_rules(session: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)) -> list[dict]:
    rows = (await session.scalars(select(CommissionRule).order_by(CommissionRule.id.desc()))).all()
    return [{"id": row.id, "scope_type": row.scope_type, "scope_id": row.scope_id, "commission_percent": float(row.commission_percent), "free_first_rides": row.free_first_rides, "is_active": row.is_active} for row in rows]


@router.post("/commission-rules", response_model=dict)
async def create_commission_rule(scope_type: str, scope_id: str, commission_percent: float = 0, free_first_rides: int = 0, session: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)) -> dict:
    row = CommissionRule(scope_type=scope_type, scope_id=scope_id, commission_percent=commission_percent, free_first_rides=free_first_rides, is_active=True, created_by_admin_id=admin.id, updated_by_admin_id=admin.id)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {"id": row.id, "scope_type": row.scope_type, "scope_id": row.scope_id, "commission_percent": float(row.commission_percent)}
