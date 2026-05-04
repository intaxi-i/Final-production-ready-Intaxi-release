from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, status
from sqlalchemy import select

from api.config import get_settings
from api.schemas import SessionData
from intaxi_bot.app.database.models import User, async_session


@dataclass(slots=True)
class TelegramUserPayload:
    tg_id: int
    full_name: str
    username: str | None


_SESSIONS: dict[str, SessionData] = {}
_SESSION_TTL_SECONDS = 60 * 60 * 24 * 14


def _now_ts() -> int:
    return int(time.time())


def validate_telegram_init_data(init_data: str, bot_token: str) -> TelegramUserPayload:
    if not bot_token:
        raise HTTPException(status_code=500, detail='BOT_TOKEN is not configured')

    pairs = parse_qsl(init_data, keep_blank_values=True)
    data = dict(pairs)
    recv_hash = data.pop('hash', None)
    if not recv_hash:
        raise HTTPException(status_code=400, detail='init_data hash is missing')

    data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(data.items(), key=lambda x: x[0]))
    secret_key = hmac.new(b'WebAppData', bot_token.encode('utf-8'), hashlib.sha256).digest()
    expected = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, recv_hash):
        raise HTTPException(status_code=401, detail='Invalid Telegram init_data signature')

    auth_date_raw = data.get('auth_date')
    if auth_date_raw and auth_date_raw.isdigit():
        auth_date = int(auth_date_raw)
        if _now_ts() - auth_date > 60 * 60 * 24:
            raise HTTPException(status_code=401, detail='Telegram init_data is expired')

    user_raw = data.get('user')
    if not user_raw:
        raise HTTPException(status_code=400, detail='Telegram user payload is missing')

    try:
        user_payload = json.loads(user_raw)
        tg_id = int(user_payload['id'])
    except Exception as exc:
        raise HTTPException(status_code=400, detail='Invalid Telegram user payload') from exc

    first_name = str(user_payload.get('first_name') or '').strip()
    last_name = str(user_payload.get('last_name') or '').strip()
    full_name = f'{first_name} {last_name}'.strip() or str(tg_id)
    username = user_payload.get('username')
    return TelegramUserPayload(tg_id=tg_id, full_name=full_name, username=username)


def create_session(tg_id: int, full_name: str, username: str | None) -> str:
    token = secrets.token_urlsafe(48)
    _SESSIONS[token] = SessionData(
        tg_id=tg_id,
        full_name=full_name,
        username=username,
        created_at=datetime.now(timezone.utc),
    )
    return token


def get_session(token: str) -> SessionData | None:
    data = _SESSIONS.get(token)
    if not data:
        return None
    age = datetime.now(timezone.utc) - data.created_at
    if age.total_seconds() > _SESSION_TTL_SECONDS:
        _SESSIONS.pop(token, None)
        return None
    return data


async def _get_user_by_tg_id(tg_id: int) -> User | None:
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))


async def get_current_user(authorization: str | None = Header(default=None)) -> User:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing Authorization header')
    parts = authorization.split(' ', 1)
    if len(parts) != 2 or parts[0].lower() != 'bearer' or not parts[1].strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid bearer token')

    session_data = get_session(parts[1].strip())
    if not session_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired session')

    user = await _get_user_by_tg_id(session_data.tg_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Session user not found')
    return user


def get_bot_token() -> str:
    return get_settings().bot_token
