from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.donation import DonationPaymentSetting
from app.schemas.donation import DonationPaymentSettingRead

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/donation-payment-settings", response_model=list[DonationPaymentSettingRead])
async def public_donation_payment_settings(
    country_code: str | None = None,
    currency: str | None = None,
    session: AsyncSession = Depends(get_db),
) -> list[DonationPaymentSettingRead]:
    query = select(DonationPaymentSetting).where(DonationPaymentSetting.is_active == True)
    if country_code:
        query = query.where(
            (DonationPaymentSetting.country_code == None)
            | (DonationPaymentSetting.country_code == country_code.lower())
        )
    if currency:
        query = query.where(
            (DonationPaymentSetting.currency == None)
            | (DonationPaymentSetting.currency == currency.upper())
        )
    rows = (
        await session.scalars(
            query.order_by(DonationPaymentSetting.sort_order.asc(), DonationPaymentSetting.id.desc())
        )
    ).all()
    return [DonationPaymentSettingRead.model_validate(row) for row in rows]
