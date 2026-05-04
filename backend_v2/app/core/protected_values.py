from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet


def _fernet_from_key(key: str) -> Fernet:
    if not key or key == "change-me":
        raise RuntimeError("strong protected value key is required")
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def protect_value(value: str | None, *, key: str) -> str | None:
    if not value:
        return None
    return _fernet_from_key(key).encrypt(value.encode("utf-8")).decode("ascii")


def unprotect_value(value: str | None, *, key: str) -> str | None:
    if not value:
        return None
    return _fernet_from_key(key).decrypt(value.encode("ascii")).decode("utf-8")


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
