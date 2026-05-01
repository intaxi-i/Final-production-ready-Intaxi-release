from __future__ import annotations

import base64
import hashlib
import hmac
import os


def protect_value(value: str | None, *, key: str) -> str | None:
    """Protect a sensitive value for storage.

    This is an authenticated obfuscation layer for V2 pre-production.
    Before public launch, replace it with a managed KMS or a vetted cryptography package.
    """
    if not value:
        return None
    if not key:
        raise RuntimeError("protected value key is required")
    nonce = os.urandom(16)
    key_bytes = hashlib.sha256(key.encode("utf-8")).digest()
    stream = hashlib.sha256(key_bytes + nonce).digest()
    raw = value.encode("utf-8")
    cipher = bytes(raw[i] ^ stream[i % len(stream)] for i in range(len(raw)))
    tag = hmac.new(key_bytes, nonce + cipher, hashlib.sha256).digest()[:16]
    return base64.urlsafe_b64encode(nonce + tag + cipher).decode("ascii")


def preview_value(value: str | None, *, left: int = 4, right: int = 4) -> str | None:
    if not value:
        return None
    clean = value.strip()
    if len(clean) <= left + right:
        return clean[:left] + "****"
    return f"{clean[:left]}...{clean[-right:]}"


def mask_card(value: str | None) -> str | None:
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) < 8:
        return "****"
    return f"{digits[:4]}********{digits[-4:]}"
