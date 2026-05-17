from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI
from fastapi.routing import APIRouter

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

RouteOverride = tuple[str, str, Callable[..., Any], Any | None]

ROUTE_OVERRIDES: tuple[RouteOverride, ...] = (
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

OVERRIDE_BY_KEY = {(method, path): (endpoint, response_model) for method, path, endpoint, response_model in ROUTE_OVERRIDES}


def _extract_methods(args: tuple[Any, ...], kwargs: dict[str, Any]) -> set[str]:
    methods = kwargs.get('methods')
    # Defensive fallback for non-standard wrappers that might pass methods positionally.
    if methods is None and len(args) >= 1 and isinstance(args[0], (list, tuple, set)):
        methods = args[0]
    return {str(method).upper() for method in (methods or [])}


def install_router_route_patch() -> None:
    if getattr(APIRouter, '_intaxi_router_route_patch_installed', False):
        return

    previous_add_api_route = APIRouter.add_api_route

    def patched_add_api_route(self, path: str, endpoint: Callable[..., Any], *args: Any, **kwargs: Any):
        methods = _extract_methods(args, kwargs)
        replacement = endpoint
        for method in methods:
            override = OVERRIDE_BY_KEY.get((method, path))
            if override:
                replacement, response_model = override
                if response_model is not None:
                    kwargs['response_model'] = response_model
                break
        return previous_add_api_route(self, path, replacement, *args, **kwargs)

    APIRouter.add_api_route = patched_add_api_route
    setattr(APIRouter, '_intaxi_router_route_patch_installed', True)


def install_runtime_route_overrides(app: FastAPI) -> None:
    """Repair already-registered routes if the router patch was installed too late."""
    if getattr(app.state, 'intaxi_runtime_route_overrides_installed', False):
        return
    app.router.routes = [
        route for route in app.router.routes
        if not any(getattr(route, 'path', None) == path and method in (getattr(route, 'methods', None) or set()) for method, path, _, _ in ROUTE_OVERRIDES)
    ]
    for method, path, endpoint, response_model in ROUTE_OVERRIDES:
        kwargs: dict[str, Any] = {'methods': [method]}
        if response_model is not None:
            kwargs['response_model'] = response_model
        app.router.add_api_route(path, endpoint, **kwargs)
    app.state.intaxi_runtime_route_overrides_installed = True
