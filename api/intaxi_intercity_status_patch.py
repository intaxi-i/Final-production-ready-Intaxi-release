from __future__ import annotations

from typing import Callable

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select

from api.auth import get_current_user
from api.schemas import IntercityStatusUpdateRequest
from api.services.lifecycle import TripActors, ensure_intercity_transition_allowed, ensure_participant_or_forbidden
from intaxi_bot.app.database.models import IntercityRequestV1, IntercityRouteV1, User, async_session


async def safe_intercity_route_status(route_id: int, payload: IntercityStatusUpdateRequest, current_user: User = Depends(get_current_user)) -> dict:
    new_status = payload.status
    async with async_session() as session:
        row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == route_id).with_for_update())
        if not row:
            raise HTTPException(status_code=404, detail='Route not found')
        ensure_participant_or_forbidden(
            current_user.tg_id,
            TripActors(creator_tg_id=row.creator_tg_id, accepted_by_tg_id=row.accepted_by_tg_id, passenger_tg_id=None, driver_tg_id=None),
        )
        ensure_intercity_transition_allowed(
            row.status or '',
            new_status,
            is_creator=current_user.tg_id == row.creator_tg_id,
            is_accepted_by=current_user.tg_id == row.accepted_by_tg_id,
        )

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
        ensure_participant_or_forbidden(
            current_user.tg_id,
            TripActors(creator_tg_id=row.creator_tg_id, accepted_by_tg_id=row.accepted_by_tg_id, passenger_tg_id=None, driver_tg_id=None),
        )
        ensure_intercity_transition_allowed(
            row.status or '',
            new_status,
            is_creator=current_user.tg_id == row.creator_tg_id,
            is_accepted_by=current_user.tg_id == row.accepted_by_tg_id,
        )

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
