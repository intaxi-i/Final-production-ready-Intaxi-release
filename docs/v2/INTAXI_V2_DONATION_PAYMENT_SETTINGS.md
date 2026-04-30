# Intaxi V2 Donation Payment Settings

Donation/support payment details are managed by admin, not hardcoded in Mini App or bot.

## Purpose

These settings are for project donations/support payments only. They are separate from:

- driver payment methods shown to passengers during trips;
- driver wallet topups;
- commission ledger;
- passenger-to-driver trip payment.

## Admin requirements

Admin panel must allow:

- create payment setting;
- edit payment setting;
- activate/deactivate payment setting;
- sort settings;
- restrict setting by country/currency;
- add card/bank transfer data;
- add digital asset wallet data;
- add public instructions;
- see masked/preview values in lists.

## Public display requirements

Public UI may show only active donation settings.

Public UI must not show inactive settings.

Sensitive full values should not be shown in admin lists. Admin edit screen may retrieve full values only through a protected endpoint after permission checks, if encryption is implemented.

## Data fields

```text
method_type: card / bank_transfer / digital_asset / other
title
country_code
currency
card_number_masked
card_number_secret
digital_asset_network
digital_asset_address_secret
digital_asset_address_preview
instructions
extra_json
sort_order
is_active
created_by_admin_id
updated_by_admin_id
disabled_at
```

## Security rules

- Do not hardcode donation cards or wallet addresses in UI.
- Do not store these values in frontend env variables.
- Do not expose inactive settings publicly.
- Add admin audit log for create/update/disable actions before production.
- Replace placeholder secret storage with encryption before production.
