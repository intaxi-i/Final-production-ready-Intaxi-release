from __future__ import annotations

import pytest

from app.domain.ride_statuses import can_transition_city_trip
from app.services.commission_service import CommissionService
from app.services.pricing_service import PricingService


@pytest.mark.parametrize(
    ("current", "target", "expected"),
    [
        ("accepted", "driver_on_way", True),
        ("accepted", "driver_arrived", True),
        ("driver_on_way", "driver_arrived", True),
        ("driver_arrived", "in_progress", True),
        ("in_progress", "completed", True),
        ("accepted", "completed", False),
        ("completed", "in_progress", False),
    ],
)
def test_city_trip_status_transitions(current: str, target: str, expected: bool) -> None:
    assert can_transition_city_trip(current, target) is expected


def test_pricing_estimate_with_coordinates() -> None:
    estimate = PricingService().estimate_city_price(
        currency="UZS",
        price_per_km=2500,
        minimum_fare=10000,
        pickup_lat=41.311081,
        pickup_lng=69.240562,
        destination_lat=41.327546,
        destination_lng=69.281181,
    )
    assert estimate.currency == "UZS"
    assert estimate.distance_km is not None
    assert estimate.duration_min is not None
    assert estimate.recommended_price is not None
    assert estimate.recommended_price >= estimate.minimum_recommended_price


def test_zero_commission_default_amount() -> None:
    assert CommissionService().calculate_commission_amount(100000, 0) == 0


def test_non_zero_commission_amount_is_calculated() -> None:
    assert CommissionService().calculate_commission_amount(100000, 5) == 5000
