from __future__ import annotations

SUPPORTED_COUNTRIES = {"uz", "tr", "kz", "sa"}
DEFAULT_COUNTRY = "uz"
DEFAULT_TARIFFS = {
    "uz": ("UZS", 2500.0),
    "tr": ("TRY", 45.0),
    "kz": ("KZT", 120.0),
    "sa": ("SAR", 2.5),
}


def normalize_country_code(value: str | None) -> str:
    code = str(value or "").strip().lower()
    return code if code in SUPPORTED_COUNTRIES else DEFAULT_COUNTRY


def country_code_from_address(address: dict | None) -> str:
    if not isinstance(address, dict):
        return DEFAULT_COUNTRY
    return normalize_country_code(address.get("country_code"))
