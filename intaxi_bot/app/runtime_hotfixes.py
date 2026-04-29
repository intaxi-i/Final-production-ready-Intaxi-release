from __future__ import annotations

import importlib
from typing import Any

KZ_TARIFF = ("KZT", 120.0)


def _country_code_with_kz(address: dict[str, Any]) -> str:
    code = str(address.get("country_code") or "").lower()
    return code if code in {"uz", "tr", "kz", "sa"} else "uz"


def _patch_city_api() -> None:
    try:
        module = importlib.import_module("api.city_flow_runtime_patch_v2")
        module.install_city_flow_runtime_patch()
    except Exception:
        return


def _patch_city_helpers() -> None:
    for module_name in ("app.database.city_flow_helper_patch", "intaxi_bot.app.database.city_flow_helper_patch"):
        try:
            module = importlib.import_module(module_name)
            module.install_city_flow_helper_patch()
            return
        except Exception:
            continue


def _patch_requests() -> None:
    for module_name in ("app.database.requests", "intaxi_bot.app.database.requests"):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        default_tariffs = getattr(module, "DEFAULT_TARIFFS", None)
        if isinstance(default_tariffs, dict):
            default_tariffs.setdefault("kz", KZ_TARIFF)


def _patch_profile() -> None:
    for module_name in ("app.handlers.profile", "intaxi_bot.app.handlers.profile"):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        setattr(module, "_country_code_from_address", _country_code_with_kz)


def apply_runtime_hotfixes() -> None:
    _patch_city_api()
    _patch_city_helpers()
    _patch_requests()
    _patch_profile()


apply_runtime_hotfixes()
