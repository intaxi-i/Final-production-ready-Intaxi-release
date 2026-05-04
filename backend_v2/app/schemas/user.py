from __future__ import annotations

from pydantic import BaseModel


class UserMe(BaseModel):
    id: int
    tg_id: int | None = None
    phone: str | None = None
    full_name: str
    username: str | None = None
    language: str
    country_code: str | None = None
    city_id: int | None = None
    active_role: str | None = None
    is_blocked: bool = False
    profile_gender: str = "unspecified"
    is_adult_confirmed: bool = False
    rating: float = 0
    rating_count: int = 0

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    language: str | None = None
    country_code: str | None = None
    city_id: int | None = None
    profile_gender: str | None = None
    is_adult_confirmed: bool | None = None


class RoleUpdate(BaseModel):
    active_role: str


class SessionResponse(BaseModel):
    session_token: str
    user: UserMe
