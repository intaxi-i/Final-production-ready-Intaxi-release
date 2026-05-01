from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from app.core.errors import DomainError
from app.core.telegram_auth import verify_telegram_webapp_init_data


def make_init_data(bot_token: str, payload: dict) -> str:
    data = {
        "auth_date": str(int(time.time())),
        "query_id": "test-query",
        "user": json.dumps(payload, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={data[key]}" for key in sorted(data))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    data["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return urlencode(data)


def test_verify_telegram_webapp_init_data_valid():
    bot_token = "123456:test-token"
    init_data = make_init_data(bot_token, {"id": 777, "first_name": "Ali", "username": "ali"})
    user = verify_telegram_webapp_init_data(
        init_data=init_data,
        bot_token=bot_token,
        max_age_seconds=86400,
    )
    assert user.tg_id == 777
    assert user.full_name == "Ali"
    assert user.username == "ali"


def test_verify_telegram_webapp_init_data_rejects_bad_hash():
    bot_token = "123456:test-token"
    init_data = make_init_data(bot_token, {"id": 777, "first_name": "Ali"}).replace("hash=", "hash=bad")
    with pytest.raises(DomainError):
        verify_telegram_webapp_init_data(
            init_data=init_data,
            bot_token=bot_token,
            max_age_seconds=86400,
        )
