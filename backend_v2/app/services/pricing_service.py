from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt


@dataclass(frozen=True, slots=True)
class PriceEstimate:
    recommended_price: float | None
    minimum_recommended_price: float | None
    distance_km: float | None
    duration_min: int | None
    currency: str


class PricingService:
    def haversine_km(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        radius_km = 6371.0
        d_lat = radians(lat2 - lat1)
        d_lng = radians(lng2 - lng1)
        a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
        c = 2 * asin(sqrt(a))
        return radius_km * c

    def estimate_city_price(
        self,
        *,
        currency: str,
        price_per_km: float,
        minimum_fare: float,
        pickup_lat: float | None,
        pickup_lng: float | None,
        destination_lat: float | None,
        destination_lng: float | None,
    ) -> PriceEstimate:
        if None in (pickup_lat, pickup_lng, destination_lat, destination_lng):
            return PriceEstimate(
                recommended_price=None,
                minimum_recommended_price=minimum_fare,
                distance_km=None,
                duration_min=None,
                currency=currency,
            )
        distance = self.haversine_km(
            float(pickup_lat),
            float(pickup_lng),
            float(destination_lat),
            float(destination_lng),
        )
        recommended = max(minimum_fare, round(distance * price_per_km, 2))
        minimum = max(0, round(recommended * 0.75, 2))
        duration_min = max(3, round(distance / 0.45))
        return PriceEstimate(
            recommended_price=recommended,
            minimum_recommended_price=minimum,
            distance_km=round(distance, 2),
            duration_min=duration_min,
            currency=currency,
        )
