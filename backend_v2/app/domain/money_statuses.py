from __future__ import annotations

from enum import StrEnum


class CounterofferStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PaymentTopupStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LedgerEntryType(StrEnum):
    TOPUP = "topup"
    COMMISSION = "commission"
    ADJUSTMENT = "adjustment"
    REFUND = "refund"
    HOLD = "hold"
    RELEASE = "release"


class LedgerDirection(StrEnum):
    CREDIT = "credit"
    DEBIT = "debit"
