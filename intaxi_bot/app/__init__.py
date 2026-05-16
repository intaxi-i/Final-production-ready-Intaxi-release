from __future__ import annotations

try:
    from app.country_bootstrap import apply_country_config
except Exception:
    apply_country_config = None

if apply_country_config is not None:
    try:
        apply_country_config()
    except Exception:
        pass
