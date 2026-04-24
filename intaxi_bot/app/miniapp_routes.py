from __future__ import annotations

import os
from urllib.parse import urlencode


def _base() -> str:
    return os.getenv("MINI_APP_URL", "https://app.intaxi.best").rstrip("/")


def _build(path: str, **params) -> str:
    clean = {k: v for k, v in params.items() if v not in (None, "", False)}
    base = _base()
    normalized = path if path.startswith("/") else f"/{path}"
    if not clean:
        return f"{base}{normalized}"
    return f"{base}{normalized}?{urlencode(clean)}"


def home_url(entry: str | None = None) -> str:
    return _build("/", entry=entry)


def city_main_url(role: str | None = None) -> str:
    return _build("/city", role=role)


def city_create_url(role: str | None = None) -> str:
    return _build("/city/create", role=role)


def city_offers_url(kind: str | None = None) -> str:
    return _build("/city/offers", kind=kind)


def city_my_orders_url() -> str:
    return _build("/city/my-orders")


def intercity_main_url(role: str | None = None) -> str:
    return _build("/intercity", role=role)


def intercity_offers_url() -> str:
    return _build("/intercity/offers")


def intercity_request_url() -> str:
    return _build("/intercity/request")


def intercity_route_url() -> str:
    return _build("/intercity/route")


def intercity_my_routes_url() -> str:
    return _build("/intercity/my-routes")


def intercity_my_requests_url() -> str:
    return _build("/intercity/my-requests")


def profile_url(entry: str | None = None) -> str:
    return _build("/profile", entry=entry)


def wallet_url() -> str:
    return _build("/wallet")


def current_trip_url(trip_type: str | None = None, trip_id: int | None = None) -> str:
    return _build("/trip/current", tripType=trip_type, tripId=trip_id)
