from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.errors import raise_domain
from app.models.user import User
from app.schemas.user import RoleUpdate, UserMe, UserProfileUpdate

router = APIRouter(prefix="/user", tags=["user"])

ALLOWED_ROLES = {"passenger", "driver", "admin"}
ALLOWED_GENDERS = {"woman", "man", "unspecified"}


@router.get("/me", response_model=UserMe)
async def get_me(current_user: User = Depends(get_current_user)) -> UserMe:
    return UserMe.model_validate(current_user)


@router.patch("/me", response_model=UserMe)
async def update_me(
    payload: UserProfileUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserMe:
    data = payload.model_dump(exclude_unset=True)
    if "profile_gender" in data and data["profile_gender"] not in ALLOWED_GENDERS:
        raise_domain("invalid_gender", "Invalid profile gender")
    for field in ["full_name", "language", "country_code", "city_id", "profile_gender", "is_adult_confirmed"]:
        if field in data:
            value = data[field]
            if field == "country_code" and isinstance(value, str):
                value = value.lower()
            setattr(current_user, field, value)
    await session.commit()
    await session.refresh(current_user)
    return UserMe.model_validate(current_user)


@router.patch("/role", response_model=UserMe)
async def update_role(
    payload: RoleUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserMe:
    if payload.active_role not in ALLOWED_ROLES:
        raise_domain("invalid_role", "Invalid active role")
    if current_user.is_blocked:
        raise_domain("user_blocked", "Blocked user cannot switch role", 403)
    current_user.active_role = payload.active_role
    await session.commit()
    await session.refresh(current_user)
    return UserMe.model_validate(current_user)
