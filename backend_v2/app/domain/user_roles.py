from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    PASSENGER = "passenger"
    DRIVER = "driver"
    ADMIN = "admin"


class ProfileGender(StrEnum):
    WOMAN = "woman"
    MAN = "man"
    UNSPECIFIED = "unspecified"


class DriverProfileStatus(StrEnum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class VehicleReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISABLED = "disabled"
