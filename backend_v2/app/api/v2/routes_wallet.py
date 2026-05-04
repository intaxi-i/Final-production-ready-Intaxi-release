from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.money import PaymentTopupRequest, WalletLedgerEntry
from app.models.user import User
from app.schemas.wallet import LedgerEntryRead, TopupCreate, TopupRead, WalletRead
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("", response_model=WalletRead)
async def get_wallet(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WalletRead:
    wallet = await WalletService().get_or_create_wallet(
        session,
        user=current_user,
        currency=current_user.country_code,
    )
    await session.commit()
    await session.refresh(wallet)
    return WalletRead.model_validate(wallet)


@router.get("/ledger", response_model=list[LedgerEntryRead])
async def wallet_ledger(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LedgerEntryRead]:
    rows = (
        await session.scalars(
            select(WalletLedgerEntry)
            .where(WalletLedgerEntry.user_id == current_user.id)
            .order_by(WalletLedgerEntry.id.desc())
            .limit(100)
        )
    ).all()
    return [LedgerEntryRead.model_validate(row) for row in rows]


@router.post("/topups", response_model=TopupRead)
async def create_topup(
    payload: TopupCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TopupRead:
    row = await WalletService().create_topup_request(
        session,
        driver=current_user,
        amount=payload.amount,
        currency=payload.currency,
        method=payload.method,
        receipt_file_id=payload.receipt_file_id,
    )
    await session.commit()
    await session.refresh(row)
    return TopupRead.model_validate(row)


@router.get("/topups", response_model=list[TopupRead])
async def my_topups(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TopupRead]:
    rows = (
        await session.scalars(
            select(PaymentTopupRequest)
            .where(PaymentTopupRequest.driver_user_id == current_user.id)
            .order_by(PaymentTopupRequest.id.desc())
            .limit(100)
        )
    ).all()
    return [TopupRead.model_validate(row) for row in rows]
