from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from app.core.errors import raise_domain


@dataclass(frozen=True, slots=True)
class TelegramWebAppUser:
    tg_id: int
    first_name: str | None
    last_name: str | None
    username: str | None
    language_code: str | None

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        name = " ".join(part for part in parts if part).strip()
        return name or self.username or f"Telegram user {self.tg_id}"


def verify_telegram_webapp_init_data(
    *,
    init_data: str,
    bot_token: str,
    max_age_seconds: int,
) -> TelegramWebAppUser:
    """Verify Telegram Mini App initData according to Telegram WebApp rules."""
    if not bot_token:
        raise_domain("telegram_auth_not_configured", "BOT_TOKEN is required for Telegram WebApp auth", 500)
    if not init_data:
        raise_domain("missing_telegram_init_data", "Missing Telegram WebApp init data", 401)

    pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise_domain("invalid_telegram_init_data", "Telegram init data hash is missing", 401)

    data_check_string = "\n".join(f"{key}={pairs[key]}" for key in sorted(pairs))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise_domain("invalid_telegram_signature", "Telegram WebApp signature is invalid", 401)

    auth_date_raw = pairs.get("auth_date")
    try:
        auth_date = int(auth_date_raw or "0")
    except ValueError:
        raise_domain("invalid_telegram_auth_date", "Telegram auth_date is invalid", 401)

    if max_age_seconds > 0 and int(time.time()) - auth_date > max_age_seconds:
        raise_domain("expired_telegram_init_data", "Telegram WebApp init data is expired", 401)

    try:
        user_payload = json.loads(pairs.get("user") or "{}")
        tg_id = int(user_payload["id"])
    except Exception:
        raise_domain("invalid_telegram_user", "Telegram user payload is invalid", 401)

    return TelegramWebAppUser(
        tg_id=tg_id,
        first_name=user_payload.get("first_name"),
        last_name=user_payload.get("last_name"),
        username=user_payload.get("username"),
        language_code=user_payload.get("language_code"),
    )
