from __future__ import annotations

import importlib

from app.country_config import DEFAULT_TARIFFS, country_code_from_address


def apply_country_config() -> None:
    for module_name in ("app.database.requests", "intaxi_bot.app.database.requests"):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        default_tariffs = getattr(module, "DEFAULT_TARIFFS", None)
        if isinstance(default_tariffs, dict):
            for country, tariff in DEFAULT_TARIFFS.items():
                default_tariffs.setdefault(country, tariff)

    for module_name in ("app.handlers.profile", "intaxi_bot.app.handlers.profile"):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        setattr(module, "_country_code_from_address", country_code_from_address)
