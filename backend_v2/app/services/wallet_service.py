from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import raise_domain
from app.models.money import PaymentTopupRequest, Wallet, WalletLedgerEntry
from app.models.user import User


class WalletService:
    async def get_or_create_wallet(self, session: AsyncSession, *, user: User, currency: str | None = None) -> Wallet:
        wallet = await session.scalar(select(Wallet).where(Wallet.user_id == user.id))
        if wallet:
            return wallet
        wallet = Wallet(
            user_id=user.id,
            balance=0,
            hold_balance=0,
            currency=currency or user.country_code,
            updated_at=datetime.now(timezone.utc),
        )
        session.add(wallet)
        await session.flush()
        return wallet

    async def add_ledger_entry(
        self,
        session: AsyncSession,
        *,
        user: User,
        entry_type: str,
        amount: float,
        currency: str,
        direction: str,
        related_type: str | None = None,
        related_id: int | None = None,
        admin_user_id: int | None = None,
        comment: str | None = None,
    ) -> WalletLedgerEntry:
        if amount <= 0:
            raise_domain("invalid_amount", "Ledger amount must be positive")
        wallet = await self.get_or_create_wallet(session, user=user, currency=currency)
        before = float(wallet.balance or 0)
        if direction == "credit":
            after = before + float(amount)
        elif direction == "debit":
            after = before - float(amount)
        else:
            raise_domain("invalid_ledger_direction", "Invalid ledger direction")
        wallet.balance = after
        wallet.currency = currency
        wallet.updated_at = datetime.now(timezone.utc)
        entry = WalletLedgerEntry(
            user_id=user.id,
            entry_type=entry_type,
            amount=float(amount),
            currency=currency,
            direction=direction,
            related_type=related_type,
            related_id=related_id,
            balance_before=before,
            balance_after=after,
            created_by_user_id=user.id if admin_user_id is None else None,
            created_by_admin_id=admin_user_id,
            comment=comment,
            created_at=datetime.now(timezone.utc),
        )
        session.add(entry)
        await session.flush()
        return entry

    async def create_topup_request(
        self,
        session: AsyncSession,
        *,
        driver: User,
        amount: float,
        currency: str,
        method: str,
        receipt_file_id: str | None = None,
    ) -> PaymentTopupRequest:
        if amount <= 0:
            raise_domain("invalid_amount", "Topup amount must be positive")
        row = PaymentTopupRequest(
            driver_user_id=driver.id,
            amount=float(amount),
            currency=currency,
            method=method,
            receipt_file_id=receipt_file_id,
            status="pending",
        )
        session.add(row)
        await session.flush()
        return row

    async def approve_topup(self, session: AsyncSession, *, topup_id: int, admin: User) -> PaymentTopupRequest:
        row = await session.scalar(select(PaymentTopupRequest).where(PaymentTopupRequest.id == topup_id))
        if not row:
            raise_domain("topup_not_found", "Topup request not found", 404)
        if row.status != "pending":
            raise_domain("topup_not_pending", "Topup request is not pending", 409)
        driver = await session.scalar(select(User).where(User.id == row.driver_user_id))
        if not driver:
            raise_domain("driver_not_found", "Driver not found", 404)
        row.status = "approved"
        row.reviewed_by_admin_id = admin.id
        row.reviewed_at = datetime.now(timezone.utc)
        await self.add_ledger_entry(
            session,
            user=driver,
            entry_type="topup",
            amount=float(row.amount),
            currency=row.currency,
            direction="credit",
            related_type="payment_topup",
            related_id=row.id,
            admin_user_id=admin.id,
        )
        await session.flush()
        return row
