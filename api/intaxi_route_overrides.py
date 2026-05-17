from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI

from api.intaxi_accept_patch import safe_city_accept
from api.intaxi_city_offers_patch import strict_city_offers
from api.intaxi_city_status_patch import strict_city_trip_status
from api.intaxi_driver_patch import strict_driver_online_update
from api.intaxi_intercity_patch import safe_intercity_accept, safe_intercity_offer_detail, safe_intercity_offers
from api.intaxi_intercity_status_patch import safe_intercity_request_status, safe_intercity_route_status
from api.intaxi_profile_patch import strict_update_profile, strict_update_role, strict_update_vehicle
from api.intaxi_safety_patch import safe_city_close, safe_current_trip, safe_history_all
from api.schemas import (
    CityAcceptResponse,
    CityOrderListResponse,
    CityTripEnvelope,
    CurrentTripResponse,
    DriverOnlineStateResponse,
    HistoryResponse,
    IntercityAcceptResponse,
    IntercityOfferEnvelope,
    IntercityOfferListResponse,
    UserEnvelope,
)

RouteSpec = tuple[str, str, Callable[..., Any], Any | None]

OVERRIDE_ROUTES: tuple[RouteSpec, ...] = (
    ('POST', '/me/profile', strict_update_profile, UserEnvelope),
    ('POST', '/me/role', strict_update_role, UserEnvelope),
    ('POST', '/me/vehicle', strict_update_vehicle, UserEnvelope),
    ('POST', '/driver/online', strict_driver_online_update, DriverOnlineStateResponse),
    ('POST', '/city/orders/{order_id}/close', safe_city_close, None),
    ('GET', '/city/offers', strict_city_offers, CityOrderListResponse),
    ('GET', '/city/orders/available', strict_city_offers, CityOrderListResponse),
    ('POST', '/city/offers/{order_id}/accept', safe_city_accept, CityAcceptResponse),
    ('POST', '/city/orders/{order_id}/accept', safe_city_accept, CityAcceptResponse),
    ('POST', '/city/trips/{trip_id}/status', strict_city_trip_status, CityTripEnvelope),
    ('GET', '/trip/current', safe_current_trip, CurrentTripResponse),
    ('GET', '/history/all', safe_history_all, HistoryResponse),
    ('GET', '/intercity/offers', safe_intercity_offers, IntercityOfferListResponse),
    ('GET', '/intercity/offers/search', safe_intercity_offers, IntercityOfferListResponse),
    ('GET', '/intercity/offers/{kind}/{item_id}', safe_intercity_offer_detail, IntercityOfferEnvelope),
    ('POST', '/intercity/offers/{kind}/{item_id}/accept', safe_intercity_accept, IntercityAcceptResponse),
    ('POST', '/intercity/routes/{route_id}/status', safe_intercity_route_status, None),
    ('POST', '/intercity/requests/{request_id}/status', safe_intercity_request_status, None),
)


def _route_methods(route: Any) -> set[str]:
    return {str(method).upper() for method in (getattr(route, 'methods', None) or set())}


def _remove_existing_route(app: FastAPI, *, method: str, path: str) -> None:
    target_method = method.upper()
    app.router.routes = [
        route for route in app.router.routes
        if not (getattr(route, 'path', None) == path and target_method in _route_methods(route))
    ]


def _add_override_route(app: FastAPI, *, method: str, path: str, endpoint: Callable[..., Any], response_model: Any | None) -> None:
    kwargs: dict[str, Any] = {'methods': [method.upper()]}
    if response_model is not None:
        kwargs['response_model'] = response_model
    app.router.add_api_route(path, endpoint, **kwargs)


def install_runtime_route_overrides(app: FastAPI) -> None:
    if getattr(app.state, 'intaxi_runtime_route_overrides_installed', False):
        return
    for method, path, endpoint, response_model in OVERRIDE_ROUTES:
        _remove_existing_route(app, method=method, path=path)
        _add_override_route(app, method=method, path=path, endpoint=endpoint, response_model=response_model)
    app.state.intaxi_runtime_route_overrides_installed = True
