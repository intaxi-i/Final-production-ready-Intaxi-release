from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI

from api.intaxi_accept_patch import safe_city_accept
from api.intaxi_driver_patch import strict_driver_online_update
from api.intaxi_intercity_patch import safe_intercity_accept, safe_intercity_offer_detail, safe_intercity_offers
from api.intaxi_intercity_status_patch import safe_intercity_request_status, safe_intercity_route_status
from api.intaxi_safety_patch import safe_city_close, safe_city_offers, safe_current_trip, safe_history_all
from api.schemas import (
    CityAcceptResponse,
    CityOrderListResponse,
    CurrentTripResponse,
    DriverOnlineStateResponse,
    HistoryResponse,
    IntercityAcceptResponse,
    IntercityOfferEnvelope,
    IntercityOfferListResponse,
)


def _extract_methods(args: tuple[Any, ...], kwargs: dict[str, Any]) -> set[str]:
    methods = kwargs.get('methods')
    # FastAPI.add_api_route signature is (path, endpoint, *, response_model=..., methods=..., ...),
    # but keep a defensive fallback for wrappers that pass methods positionally.
    if methods is None and len(args) >= 2 and isinstance(args[1], (list, tuple, set)):
        methods = args[1]
    return {str(m).upper() for m in (methods or [])}


def _route_kwargs(kwargs: dict[str, Any], response_model: Any | None = None) -> dict[str, Any]:
    data = dict(kwargs)
    if response_model is not None:
        data['response_model'] = response_model
    return data


def _route_exists(self: FastAPI, path: str, methods: set[str]) -> bool:
    for route in getattr(self.router, 'routes', []):
        if getattr(route, 'path', None) != path:
            continue
        route_methods = {str(m).upper() for m in (getattr(route, 'methods', None) or [])}
        if methods <= route_methods:
            return True
    return False


def _safe_alias(self: FastAPI, path: str, endpoint: Callable, *, methods: list[str], response_model: Any | None = None) -> None:
    method_set = {str(m).upper() for m in methods}
    if not _route_exists(self, path, method_set):
        self.router.add_api_route(path, endpoint, methods=methods, response_model=response_model)


def _direct_add(self: FastAPI, path: str, endpoint: Callable, args: tuple[Any, ...], kwargs: dict[str, Any], response_model: Any | None = None):
    self.router.add_api_route(path, endpoint, *args, **_route_kwargs(kwargs, response_model))
    return None


def install_intaxi_terminal_patch() -> None:
    if getattr(FastAPI, '_intaxi_terminal_patch_installed', False):
        return
    previous_add_api_route = FastAPI.add_api_route

    def patched_add_api_route(self, path: str, endpoint: Callable, *args: Any, **kwargs: Any):
        methods = _extract_methods(args, kwargs)

        if path == '/driver/online' and 'POST' in methods:
            return _direct_add(self, path, strict_driver_online_update, args, kwargs, DriverOnlineStateResponse)

        if path == '/city/orders/{order_id}/close' and 'POST' in methods:
            return _direct_add(self, path, safe_city_close, args, kwargs)

        if path == '/city/offers' and 'GET' in methods:
            result = _direct_add(self, path, safe_city_offers, args, kwargs, CityOrderListResponse)
            _safe_alias(self, '/city/orders/available', safe_city_offers, methods=['GET'], response_model=CityOrderListResponse)
            return result

        if path == '/city/offers/{order_id}/accept' and 'POST' in methods:
            result = _direct_add(self, path, safe_city_accept, args, kwargs, CityAcceptResponse)
            _safe_alias(self, '/city/orders/{order_id}/accept', safe_city_accept, methods=['POST'], response_model=CityAcceptResponse)
            return result

        if path == '/trip/current' and 'GET' in methods:
            return _direct_add(self, path, safe_current_trip, args, kwargs, CurrentTripResponse)

        if path == '/history/all' and 'GET' in methods:
            return _direct_add(self, path, safe_history_all, args, kwargs, HistoryResponse)

        if path == '/intercity/offers' and 'GET' in methods:
            result = _direct_add(self, path, safe_intercity_offers, args, kwargs, IntercityOfferListResponse)
            _safe_alias(self, '/intercity/offers/search', safe_intercity_offers, methods=['GET'], response_model=IntercityOfferListResponse)
            return result

        if path == '/intercity/offers/{kind}/{item_id}' and 'GET' in methods:
            return _direct_add(self, path, safe_intercity_offer_detail, args, kwargs, IntercityOfferEnvelope)

        if path == '/intercity/offers/{kind}/{item_id}/accept' and 'POST' in methods:
            return _direct_add(self, path, safe_intercity_accept, args, kwargs, IntercityAcceptResponse)

        if path == '/intercity/routes/{route_id}/status' and 'POST' in methods:
            return _direct_add(self, path, safe_intercity_route_status, args, kwargs)

        if path == '/intercity/requests/{request_id}/status' and 'POST' in methods:
            return _direct_add(self, path, safe_intercity_request_status, args, kwargs)

        return previous_add_api_route(self, path, endpoint, *args, **kwargs)

    FastAPI.add_api_route = patched_add_api_route
    setattr(FastAPI, '_intaxi_terminal_patch_installed', True)
