from __future__ import annotations

from typing import Callable

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select

from api.auth import get_current_user
from api.schemas import IntercityStatusUpdateRequest
from intaxi_bot.app.database.models import IntercityRequestV1, IntercityRouteV1, User, async_session

DRIVER_STATUSES = {'in_progress', 'completed', 'cancelled'}
PASSENGER_STATUSES = {'cancelled', 'closed'}
OWNER_ACTIVE_STATUSES = {'cancelled', 'closed'}
FINAL_STATUSES = {'completed', 'cancelled', 'closed'}


def _is_final(status: str | None) -> bool:
    return (status or '') in FINAL_STATUSES


async def safe_intercity_route_status(route_id: int, payload: IntercityStatusUpdateRequest, current_user: User = Depends(get_current_user)) -> dict:
    new_status = payload.status
    async with async_session() as session:
        row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == route_id).with_for_update())
        if not row:
            raise HTTPException(status_code=404, detail='Route not found')
        if current_user.tg_id not in {row.creator_tg_id, row.accepted_by_tg_id}:
            raise HTTPException(status_code=403, detail='Forbidden')
        if _is_final(row.status):
            raise HTTPException(status_code=409, detail='Route is already finished')

        is_driver = current_user.tg_id == row.creator_tg_id
        is_passenger = current_user.tg_id == row.accepted_by_tg_id
        if row.status == 'active':
            if not is_driver or new_status not in OWNER_ACTIVE_STATUSES:
                raise HTTPException(status_code=403, detail='Unsupported status transition')
        elif is_driver:
            if new_status not in DRIVER_STATUSES:
                raise HTTPException(status_code=403, detail='Unsupported status transition')
        elif is_passenger:
            if new_status not in PASSENGER_STATUSES:
                raise HTTPException(status_code=403, detail='Unsupported status transition')
        else:
            raise HTTPException(status_code=403, detail='Forbidden')

        row.status = new_status
        if new_status == 'completed':
            driver = await session.scalar(select(User).where(User.tg_id == row.creator_tg_id))
            if driver and driver.is_verified:
                driver.commission_due = 0.0
        await session.commit()
        return {'id': row.id, 'status': row.status}


async def safe_intercity_request_status(request_id: int, payload: IntercityStatusUpdateRequest, current_user: User = Depends(get_current_user)) -> dict:
    new_status = payload.status
    async with async_session() as session:
        row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == request_id).with_for_update())
        if not row:
            raise HTTPException(status_code=404, detail='Request not found')
        if current_user.tg_id not in {row.creator_tg_id, row.accepted_by_tg_id}:
            raise HTTPException(status_code=403, detail='Forbidden')
        if _is_final(row.status):
            raise HTTPException(status_code=409, detail='Request is already finished')

        is_passenger = current_user.tg_id == row.creator_tg_id
        is_driver = current_user.tg_id == row.accepted_by_tg_id
        if row.status == 'active':
            if not is_passenger or new_status not in OWNER_ACTIVE_STATUSES:
                raise HTTPException(status_code=403, detail='Unsupported status transition')
        elif is_driver:
            if new_status not in DRIVER_STATUSES:
                raise HTTPException(status_code=403, detail='Unsupported status transition')
        elif is_passenger:
            if new_status not in PASSENGER_STATUSES:
                raise HTTPException(status_code=403, detail='Unsupported status transition')
        else:
            raise HTTPException(status_code=403, detail='Forbidden')

        row.status = new_status
        if new_status == 'completed' and row.accepted_by_tg_id:
            driver = await session.scalar(select(User).where(User.tg_id == row.accepted_by_tg_id))
            if driver and driver.is_verified:
                driver.commission_due = 0.0
        await session.commit()
        return {'id': row.id, 'status': row.status}


def install_intaxi_intercity_status_patch() -> None:
    if getattr(FastAPI, '_intaxi_intercity_status_patch_installed', False):
        return
    previous_add_api_route = FastAPI.add_api_route

    def patched_add_api_route(self, path: str, endpoint: Callable, *args, **kwargs):
        methods = {str(m).upper() for m in (kwargs.get('methods') or [])}
        replacement = endpoint
        if path == '/intercity/routes/{route_id}/status' and 'POST' in methods:
            replacement = safe_intercity_route_status
        elif path == '/intercity/requests/{request_id}/status' and 'POST' in methods:
            replacement = safe_intercity_request_status
        return previous_add_api_route(self, path, replacement, *args, **kwargs)

    FastAPI.add_api_route = patched_add_api_route
    setattr(FastAPI, '_intaxi_intercity_status_patch_installed', True)
