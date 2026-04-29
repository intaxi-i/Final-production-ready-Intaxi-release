from __future__ import annotations

from enum import StrEnum


class RideMode(StrEnum):
    REGULAR = "regular"
    WOMEN = "women"


class CityOrderStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    DISPUTED = "disputed"


class CityTripStatus(StrEnum):
    ACCEPTED = "accepted"
    DRIVER_ON_WAY = "driver_on_way"
    DRIVER_ARRIVED = "driver_arrived"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


CITY_TRIP_TRANSITIONS: dict[str, set[str]] = {
    "accepted": {"driver_on_way", "driver_arrived", "cancelled", "disputed"},
    "driver_on_way": {"driver_arrived", "cancelled", "disputed"},
    "driver_arrived": {"in_progress", "cancelled", "disputed"},
    "in_progress": {"completed", "cancelled", "disputed"},
    "completed": {"disputed"},
    "cancelled": {"disputed"},
    "disputed": {"completed", "cancelled"},
}

TRIP_TO_ORDER_STATUS: dict[str, str] = {
    "accepted": "accepted",
    "driver_on_way": "accepted",
    "driver_arrived": "accepted",
    "in_progress": "in_progress",
    "completed": "completed",
    "cancelled": "cancelled",
    "disputed": "disputed",
}


def can_transition_city_trip(current: str, target: str) -> bool:
    return current == target or target in CITY_TRIP_TRANSITIONS.get(current, set())
