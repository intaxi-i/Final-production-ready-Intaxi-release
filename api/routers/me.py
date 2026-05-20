from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from api.auth import get_current_user
from api.deps import require_verified_driver, set_user_active_role, user_to_me
from api.schemas import (
    UpdateProfileRequest,
    UpdateRoleRequest,
    UpdateVehicleRequest,
    UserEnvelope,
    UserMe,
)
from intaxi_bot.app.database.models import User, async_session
from intaxi_bot.app.database.requests import register_vehicle, set_user_reg

router = APIRouter(tags=['me'])


@router.get('/me', response_model=UserMe)
async def me(current_user: User = Depends(get_current_user)) -> UserMe:
    return await user_to_me(current_user)


@router.post('/me/profile', response_model=UserEnvelope)
async def update_profile(payload: UpdateProfileRequest, current_user: User = Depends(get_current_user)) -> UserEnvelope:
    language = payload.language or current_user.language or 'ru'
    country = payload.country if payload.country is not None else (current_user.country or '')
    city = payload.city if payload.city is not None else (current_user.city or '')
    await set_user_reg(current_user.tg_id, language=language, country=country, city=city)
    async with async_session() as session:
        refreshed = await session.scalar(select(User).where(User.tg_id == current_user.tg_id))
    if not refreshed:
        raise HTTPException(status_code=404, detail='User not found after update')
    return UserEnvelope(user=await user_to_me(refreshed))


@router.post('/me/role', response_model=UserEnvelope)
async def update_role(payload: UpdateRoleRequest, current_user: User = Depends(get_current_user)) -> UserEnvelope:
    if payload.active_role not in {'driver', 'passenger'}:
        raise HTTPException(status_code=400, detail='active_role must be driver or passenger')
    if payload.active_role == 'driver':
        await require_verified_driver(current_user, detail='Only verified drivers can switch to driver mode')
    updated = await set_user_active_role(current_user.tg_id, payload.active_role)
    if not updated:
        raise HTTPException(status_code=404, detail='User not found')
    return UserEnvelope(user=await user_to_me(updated))


@router.post('/me/vehicle', response_model=UserEnvelope)
async def update_vehicle(payload: UpdateVehicleRequest, current_user: User = Depends(get_current_user)) -> UserEnvelope:
    if not payload.brand or not payload.model or not payload.plate:
        raise HTTPException(status_code=400, detail='brand, model and plate are required')
    vehicle_data = payload.model_dump(exclude_none=True)
    await register_vehicle(current_user.tg_id, vehicle_data)
    async with async_session() as session:
        refreshed = await session.scalar(select(User).where(User.tg_id == current_user.tg_id))
    if not refreshed:
        raise HTTPException(status_code=404, detail='User not found')
    return UserEnvelope(user=await user_to_me(refreshed))
