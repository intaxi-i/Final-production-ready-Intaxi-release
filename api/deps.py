from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select

from api.schemas import UserMe, VehicleInfo
from intaxi_bot.app.database.models import User, Vehicle, async_session


async def require_verified_driver(current_user: User, *, detail: str = 'Only verified drivers can use this feature') -> None:
    """Guard endpoints that are available only to verified drivers."""
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail=detail)


def vehicle_to_schema(vehicle: Vehicle | None) -> VehicleInfo | None:
    if not vehicle:
        return None
    return VehicleInfo(
        brand=vehicle.brand,
        model=vehicle.model,
        plate=vehicle.plate,
        color=vehicle.color,
        capacity=vehicle.capacity,
        vehicle_class=vehicle.vehicle_class,
    )


async def user_to_me(user: User) -> UserMe:
    async with async_session() as session:
        db_user = await session.scalar(select(User).where(User.id == user.id))
        if not db_user:
            raise HTTPException(status_code=404, detail='User not found')
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == db_user.id))

    return UserMe(
        tg_id=db_user.tg_id,
        full_name=db_user.full_name,
        username=db_user.username,
        language=db_user.language,
        country=db_user.country,
        city=db_user.city,
        balance=float(db_user.balance or 0),
        commission_due=0.0,
        free_rides_left=0,
        active_role=db_user.active_role,
        is_verified=bool(db_user.is_verified),
        vehicle=vehicle_to_schema(vehicle),
    )


async def set_user_active_role(tg_id: int, active_role: str) -> User | None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return None
        user.active_role = active_role
        await session.commit()
        await session.refresh(user)
        return user
