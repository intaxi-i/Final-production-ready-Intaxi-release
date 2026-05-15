from __future__ import annotations

import importlib
from typing import Any

KZ_TARIFF = ("KZT", 120.0)
SUPPORTED_COUNTRIES = {"uz", "tr", "kz", "sa"}


def _country_code_with_kz(address: dict[str, Any]) -> str:
    code = str(address.get("country_code") or "").lower()
    return code if code in SUPPORTED_COUNTRIES else "uz"


def _patch_requests_country_defaults() -> None:
    for module_name in ("app.database.requests", "intaxi_bot.app.database.requests"):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        default_tariffs = getattr(module, "DEFAULT_TARIFFS", None)
        if isinstance(default_tariffs, dict):
            default_tariffs.setdefault("kz", KZ_TARIFF)


def _patch_profile_country_detection() -> None:
    for module_name in ("app.handlers.profile", "intaxi_bot.app.handlers.profile"):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        setattr(module, "_country_code_from_address", _country_code_with_kz)


def apply_runtime_hotfixes() -> None:
    # Temporary compatibility only: keep country support consistent until the
    # large canonical modules are safely updated without replacing their full
    # contents through the GitHub contents API.
    _patch_requests_country_defaults()
    _patch_profile_country_detection()


apply_runtime_hotfixes()
