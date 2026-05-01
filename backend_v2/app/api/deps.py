from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import raise_domain
from app.core.telegram_auth import verify_telegram_webapp_init_data
from app.models.user import User


async def _user_by_id(session: AsyncSession, user_id: int) -> User:
    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise_domain("user_not_found", "User not found", 401)
    return user


async def _user_by_telegram_init_data(session: AsyncSession, init_data: str) -> User:
    settings = get_settings()
    tg_user = verify_telegram_webapp_init_data(
        init_data=init_data,
        bot_token=settings.bot_token,
        max_age_seconds=86400,
    )
    user = await session.scalar(select(User).where(User.tg_id == tg_user.tg_id))
    if not user:
        user = User(
            tg_id=tg_user.tg_id,
            full_name=tg_user.full_name,
            username=tg_user.username,
            language=tg_user.language_code or "ru",
            active_role="passenger",
        )
        session.add(user)
        await session.flush()
    else:
        user.full_name = tg_user.full_name or user.full_name
        user.username = tg_user.username
        if tg_user.language_code:
            user.language = tg_user.language_code
    await session.commit()
    await session.refresh(user)
    return user


async def get_current_user(
    authorization: str | None = Header(default=None),
    x_telegram_init_data: str | None = Header(default=None),
    x_dev_user_id: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> User:
    settings = get_settings()

    if x_telegram_init_data:
        return await _user_by_telegram_init_data(session, x_telegram_init_data)

    if x_dev_user_id and not settings.is_production:
        try:
            return await _user_by_id(session, int(x_dev_user_id))
        except ValueError:
            raise_domain("invalid_dev_user", "Invalid development user id", 401)

    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise_domain("invalid_authorization", "Invalid Authorization header", 401)
        token = parts[1].strip()
        if token.startswith("dev:"):
            if settings.is_production:
                raise_domain("dev_auth_disabled", "Development auth is disabled in production", 401)
            try:
                return await _user_by_id(session, int(token.split(":", 1)[1]))
            except ValueError:
                raise_domain("invalid_auth_token", "Invalid development token", 401)
        if token.startswith("tgwebapp:"):
            return await _user_by_telegram_init_data(session, token.split(":", 1)[1])

    raise_domain("session_required", "Telegram WebApp session is required", 401)


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.active_role != "admin":
        raise_domain("admin_required", "Admin permission required", 403)
    return current_user
