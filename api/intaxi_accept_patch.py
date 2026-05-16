from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, FastAPI, HTTPException

from api.auth import get_current_user
from api.order_actions import accept_city_offer_for_user
from api.schemas import CityAcceptResponse
from intaxi_bot.app.database.models import User


async def safe_city_accept(order_id: int, current_user: User = Depends(get_current_user)) -> CityAcceptResponse:
    trip = await accept_city_offer_for_user(order_id, current_user.tg_id)
    if not trip:
        raise HTTPException(status_code=403, detail='Order is not available for acceptance')
    return CityAcceptResponse(trip_id=trip.id, status=trip.status or 'accepted')


def install_intaxi_accept_patch() -> None:
    if getattr(FastAPI, '_intaxi_accept_patch_installed', False):
        return
    previous_add_api_route = FastAPI.add_api_route

    def patched_add_api_route(self, path: str, endpoint: Callable, *args: Any, **kwargs: Any):
        methods = {str(m).upper() for m in (kwargs.get('methods') or [])}
        replacement = endpoint
        if path == '/city/offers/{order_id}/accept' and 'POST' in methods:
            replacement = safe_city_accept
        return previous_add_api_route(self, path, replacement, *args, **kwargs)

    FastAPI.add_api_route = patched_add_api_route
    setattr(FastAPI, '_intaxi_accept_patch_installed', True)
