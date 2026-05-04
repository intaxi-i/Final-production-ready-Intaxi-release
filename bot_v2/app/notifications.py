from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CityOrderNotification:
    order_id: int
    pickup_address: str
    destination_address: str
    price: float
    currency: str
    distance_km: float | None = None


def format_city_order_notification(item: CityOrderNotification) -> str:
    distance = f"\nDistance: {item.distance_km} km" if item.distance_km is not None else ""
    return (
        "New city order\n\n"
        f"A: {item.pickup_address}\n"
        f"B: {item.destination_address}\n"
        f"Price: {item.price} {item.currency}"
        f"{distance}"
    )


def current_trip_url(base_miniapp_url: str, trip_id: int, trip_type: str = "city") -> str:
    clean = base_miniapp_url.rstrip("/")
    return f"{clean}/trip/current?tripType={trip_type}&tripId={trip_id}"
