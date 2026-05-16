from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, FastAPI, HTTPException

from api.auth import get_current_user
from api.order_actions import close_city_order_for_user
from intaxi_bot.app.database.models import User


async def safe_city_close(order_id: int, current_user: User = Depends(get_current_user)) -> dict:
    row = await close_city_order_for_user(order_id, current_user.tg_id)
    if not row:
        raise HTTPException(status_code=404, detail='Order not found')
    return {'id': row.id, 'status': row.status}


def install_intaxi_safety_patch() -> None:
    if getattr(FastAPI, '_intaxi_safety_patch_installed', False):
        return
    previous_add_api_route = FastAPI.add_api_route

    def patched_add_api_route(self, path: str, endpoint: Callable, *args: Any, **kwargs: Any):
        methods = {str(m).upper() for m in (kwargs.get('methods') or [])}
        replacement = endpoint
        if path == '/city/orders/{order_id}/close' and 'POST' in methods:
            replacement = safe_city_close
        return previous_add_api_route(self, path, replacement, *args, **kwargs)

    FastAPI.add_api_route = patched_add_api_route
    setattr(FastAPI, '_intaxi_safety_patch_installed', True)
