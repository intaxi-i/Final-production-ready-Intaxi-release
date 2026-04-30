from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.core.errors import raise_domain
from app.models.commission import CommissionRule
from app.models.donation import DonationPaymentSetting
from app.models.driver import DriverProfile
from app.models.money import PaymentTopupRequest
from app.models.user import User
from app.schemas.donation import (
    DonationPaymentSettingCreate,
    DonationPaymentSettingRead,
    DonationPaymentSettingUpdate,
)
from app.services.admin_audit_service import AdminAuditService
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/admin", tags=["admin"])


def _mask_card(card_number: str | None) -> str | None:
    if not card_number:
        return None
    digits = ''.join(ch for ch in card_number if ch.isdigit())
    if len(digits) < 8:
        return '****'
    return f"{digits[:4]}********{digits[-4:]}"


def _preview_secret(value: str | None) -> str | None:
    if not value:
        return None
    clean = value.strip()
    if len(clean) <= 12:
        return clean[:4] + '****'
    return f"{clean[:6]}...{clean[-6:]}"


@router.get("/dashboard", response_model=dict)
async def admin_dashboard(session: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)) -> dict:
    pending_drivers = len((await session.scalars(select(DriverProfile).where(DriverProfile.status == "pending"))).all())
    pending_topups = len((await session.scalars(select(PaymentTopupRequest).where(PaymentTopupRequest.status == "pending"))).all())
    donation_methods = len((await session.scalars(select(DonationPaymentSetting).where(DonationPaymentSetting.is_active == True))).all())
    return {"pending_drivers": pending_drivers, "pending_topups": pending_topups, "active_donation_methods": donation_methods}


@router.get("/drivers/pending", response_model=list[dict])
async def pending_drivers(session: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)) -> list[dict]:
    rows = (await session.scalars(select(DriverProfile).where(DriverProfile.status == "pending"))).all()
    return [{"id": row.id, "user_id": row.user_id, "country_code": row.country_code, "city_id": row.city_id} for row in rows]


@router.post("/drivers/{driver_profile_id}/approve", response_model=dict)
async def approve_driver(driver_profile_id: int, session: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)) -> dict:
    row = await session.scalar(select(DriverProfile).where(DriverProfile.id == driver_profile_id))
    if not row:
        raise_domain("driver_profile_not_found", "Driver profile not found", 404)
    before = {"status": row.status, "reviewed_by_admin_id": row.reviewed_by_admin_id}
    row.status = "approved"
    row.reviewed_by_admin_id = admin.id
    await AdminAuditService().write(session, admin=admin, action="driver_profile.approve", entity_type="driver_profile", entity_id=row.id, before=before, after={"status": row.status, "reviewed_by_admin_id": row.reviewed_by_admin_id})
    await session.commit()
    return {"id": row.id, "status": row.status}


@router.post("/payments/{payment_id}/approve", response_model=dict)
async def approve_payment(payment_id: int, session: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)) -> dict:
    row = await WalletService().approve_topup(session, topup_id=payment_id, admin=admin)
    await AdminAuditService().write(session, admin=admin, action="payment_topup.approve", entity_type="payment_topup", entity_id=row.id, after={"status": row.status, "amount": float(row.amount), "currency": row.currency})
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
    await session.flush()
    await AdminAuditService().write(session, admin=admin, action="commission_rule.create", entity_type="commission_rule", entity_id=row.id, after={"scope_type": row.scope_type, "scope_id": row.scope_id, "commission_percent": float(row.commission_percent), "free_first_rides": row.free_first_rides, "is_active": row.is_active})
    await session.commit()
    await session.refresh(row)
    return {"id": row.id, "scope_type": row.scope_type, "scope_id": row.scope_id, "commission_percent": float(row.commission_percent)}


@router.get("/donation-payment-settings", response_model=list[DonationPaymentSettingRead])
async def list_donation_payment_settings(session: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)) -> list[DonationPaymentSettingRead]:
    rows = (await session.scalars(select(DonationPaymentSetting).order_by(DonationPaymentSetting.sort_order.asc(), DonationPaymentSetting.id.desc()))).all()
    return [DonationPaymentSettingRead.model_validate(row) for row in rows]


@router.post("/donation-payment-settings", response_model=DonationPaymentSettingRead)
async def create_donation_payment_setting(payload: DonationPaymentSettingCreate, session: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)) -> DonationPaymentSettingRead:
    row = DonationPaymentSetting(
        method_type=payload.method_type,
        title=payload.title,
        country_code=payload.country_code.lower() if payload.country_code else None,
        currency=payload.currency,
        card_number_masked=_mask_card(payload.card_number),
        card_number_secret=payload.card_number,
        card_holder_name=payload.card_holder_name,
        bank_name=payload.bank_name,
        digital_asset_network=payload.digital_asset_network,
        digital_asset_address_secret=payload.digital_asset_address,
        digital_asset_address_preview=_preview_secret(payload.digital_asset_address),
        instructions=payload.instructions,
        extra_json=payload.extra_json,
        sort_order=payload.sort_order,
        is_active=payload.is_active,
        created_by_admin_id=admin.id,
        updated_by_admin_id=admin.id,
    )
    session.add(row)
    await session.flush()
    await AdminAuditService().write(session, admin=admin, action="donation_payment_setting.create", entity_type="donation_payment_setting", entity_id=row.id, after={"method_type": row.method_type, "title": row.title, "country_code": row.country_code, "currency": row.currency, "is_active": row.is_active})
    await session.commit()
    await session.refresh(row)
    return DonationPaymentSettingRead.model_validate(row)


@router.patch("/donation-payment-settings/{setting_id}", response_model=DonationPaymentSettingRead)
async def update_donation_payment_setting(setting_id: int, payload: DonationPaymentSettingUpdate, session: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)) -> DonationPaymentSettingRead:
    row = await session.scalar(select(DonationPaymentSetting).where(DonationPaymentSetting.id == setting_id))
    if not row:
        raise_domain("donation_payment_setting_not_found", "Donation payment setting not found", 404)
    before = {"title": row.title, "country_code": row.country_code, "currency": row.currency, "is_active": row.is_active, "sort_order": row.sort_order}
    data = payload.model_dump(exclude_unset=True)
    for field in ["title", "currency", "card_holder_name", "bank_name", "digital_asset_network", "instructions", "extra_json", "sort_order", "is_active"]:
        if field in data:
            setattr(row, field, data[field])
    if "country_code" in data:
        row.country_code = data["country_code"].lower() if data["country_code"] else None
    if "card_number" in data:
        row.card_number_masked = _mask_card(data["card_number"])
        row.card_number_secret = data["card_number"]
    if "digital_asset_address" in data:
        row.digital_asset_address_secret = data["digital_asset_address"]
        row.digital_asset_address_preview = _preview_secret(data["digital_asset_address"])
    if "is_active" in data and data["is_active"] is False:
        row.disabled_at = datetime.now(timezone.utc)
    row.updated_by_admin_id = admin.id
    await session.flush()
    after = {"title": row.title, "country_code": row.country_code, "currency": row.currency, "is_active": row.is_active, "sort_order": row.sort_order}
    await AdminAuditService().write(session, admin=admin, action="donation_payment_setting.update", entity_type="donation_payment_setting", entity_id=row.id, before=before, after=after)
    await session.commit()
    await session.refresh(row)
    return DonationPaymentSettingRead.model_validate(row)
