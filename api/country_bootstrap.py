from __future__ import annotations

from intaxi_bot.app.country_config import DEFAULT_TARIFFS


def apply_country_config() -> None:
    try:
        from intaxi_bot.app.database import requests as rq
    except Exception:
        return
    default_tariffs = getattr(rq, "DEFAULT_TARIFFS", None)
    if not isinstance(default_tariffs, dict):
        return
    for country, tariff in DEFAULT_TARIFFS.items():
        default_tariffs.setdefault(country, tariff)
