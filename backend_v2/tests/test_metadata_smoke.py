from __future__ import annotations

from app.core.database import Base
from app import models  # noqa: F401


def test_v2_metadata_contains_expected_tables() -> None:
    expected = {
        "users_v2",
        "driver_profiles_v2",
        "vehicles_v2",
        "driver_online_states_v2",
        "driver_payment_methods_v2",
        "city_orders_v2",
        "city_counteroffers_v2",
        "city_trips_v2",
        "intercity_requests_v2",
        "intercity_routes_v2",
        "intercity_trips_v2",
        "wallets_v2",
        "wallet_ledger_entries_v2",
        "commission_rules_v2",
        "payment_topup_requests_v2",
        "donation_payment_settings_v2",
        "admin_audit_logs_v2",
        "domain_events_v2",
        "support_tickets_v2",
        "ratings_v2",
        "countries_v2",
        "cities_v2",
    }
    assert expected.issubset(set(Base.metadata.tables.keys()))


def test_donation_settings_are_separate_from_driver_payment_methods() -> None:
    donation = Base.metadata.tables["donation_payment_settings_v2"]
    driver_payment = Base.metadata.tables["driver_payment_methods_v2"]
    assert "driver_user_id" not in donation.c
    assert "driver_user_id" in driver_payment.c
    assert "digital_asset_address_preview" in donation.c
