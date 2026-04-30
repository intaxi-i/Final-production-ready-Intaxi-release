from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import raise_domain
from app.models.user import User


async def get_current_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Temporary V2 auth dependency.

    During early V2 development this accepts `Bearer dev:<user_id>`.
    Production rejects development tokens until Telegram WebApp/session auth is implemented.
    """
    if not authorization:
        raise_domain("missing_authorization", "Missing Authorization header", 401)
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise_domain("invalid_authorization", "Invalid Authorization header", 401)
    token = parts[1].strip()
    settings = get_settings()
    if token.startswith("dev:"):
        if settings.is_production:
            raise_domain("dev_auth_disabled", "Development auth is disabled in production", 401)
        try:
            user_id = int(token.split(":", 1)[1])
        except Exception:
            raise_domain("invalid_auth_token", "Invalid development token", 401)
        user = await session.scalar(select(User).where(User.id == user_id))
        if not user:
            raise_domain("user_not_found", "User not found", 401)
        return user
    raise_domain("unsupported_auth_token", "Real session auth is not implemented yet", 401)


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.active_role != "admin":
        raise_domain("admin_required", "Admin permission required", 403)
    return current_user
