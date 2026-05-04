from __future__ import annotations

from pydantic import BaseModel, Field


class WalletRead(BaseModel):
    user_id: int
    balance: float
    hold_balance: float
    currency: str | None = None

    model_config = {"from_attributes": True}


class TopupCreate(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(min_length=2, max_length=8)
    method: str = Field(min_length=2, max_length=32)
    receipt_file_id: str | None = None


class TopupRead(BaseModel):
    id: int
    driver_user_id: int
    amount: float
    currency: str
    method: str
    receipt_file_id: str | None = None
    status: str
    rejection_reason: str | None = None

    model_config = {"from_attributes": True}


class LedgerEntryRead(BaseModel):
    id: int
    user_id: int
    entry_type: str
    amount: float
    currency: str
    direction: str
    related_type: str | None = None
    related_id: int | None = None
    balance_before: float
    balance_after: float
    comment: str | None = None

    model_config = {"from_attributes": True}
