# Intaxi V2 Foundation Review

This document records the first review pass after creating the V2 clean architecture foundation.

## Review scope

Reviewed and corrected the first V2 foundation layer:

- docs/v2 specifications;
- backend_v2 core structure;
- SQLAlchemy model relationships and field naming;
- API route wiring;
- admin mutation coverage;
- donation payment settings requirement;
- dev auth safety;
- public config exposure rules.

## Fixes applied

### 1. Intercity date/time naming

The first intercity model used fields named `date` and `time`. These were renamed to:

- `ride_date`
- `ride_time`

Reason: avoid ambiguity with Python/date concepts and make API/model purpose clearer.

Affected files:

- backend_v2/app/models/intercity.py
- backend_v2/app/services/intercity_service.py
- backend_v2/app/api/v2/routes_intercity.py

### 2. API v2 package marker

Added:

- backend_v2/app/api/v2/__init__.py

Reason: keep package imports explicit and predictable.

### 3. Public donation settings route

Added public read-only route:

- GET /api/v2/public/donation-payment-settings

Rules:

- returns only active settings;
- supports optional country/currency filters;
- returns masked/preview values only.

### 4. Donation payment settings admin support

Added admin-managed settings for donation/support payment details.

Files:

- backend_v2/app/models/donation.py
- backend_v2/app/schemas/donation.py
- backend_v2/app/api/v2/routes_public.py
- backend_v2/app/api/v2/routes_admin.py
- docs/v2/INTAXI_V2_DONATION_PAYMENT_SETTINGS.md

Admin endpoints:

- GET /api/v2/admin/donation-payment-settings
- POST /api/v2/admin/donation-payment-settings
- PATCH /api/v2/admin/donation-payment-settings/{setting_id}

### 5. Donation settings separated from trip/wallet logic

Donation payment settings are separate from:

- driver payment methods;
- driver wallet topups;
- passenger-to-driver trip payment;
- commission ledger.

### 6. Admin audit service

Added:

- backend_v2/app/services/admin_audit_service.py

Audit records are now written for:

- driver approval;
- driver rejection;
- woman-mode driver approval;
- payment approval;
- payment rejection;
- commission rule creation;
- donation payment setting creation/update.

### 7. Admin action coverage restored

Restored admin endpoints:

- reject driver;
- approve woman-mode driver;
- reject payment topup.

### 8. Dev auth production guard

Updated:

- backend_v2/app/api/deps.py

Development token format `Bearer dev:<user_id>` is allowed only outside production.

In production, dev auth is rejected.

### 9. Ambiguous ORM relationships removed

The initial `User` and `DriverProfile` relationship mapping could become ambiguous because several models reference `users_v2` multiple times.

Fix:

- removed fragile relationship definitions from User/DriverProfile for now;
- services already query explicitly by foreign key;
- relationships can be reintroduced later with explicit `foreign_keys` after compile/runtime validation.

### 10. Timestamp defaults added

Added safer defaults to:

- admin audit log created_at;
- domain event created_at;
- wallet updated_at;
- wallet ledger created_at;
- driver online state updated_at.

## Known limitations after this review

Still not fully verified by runtime execution in this environment:

- Python imports;
- SQLAlchemy mapper configuration;
- Alembic autogenerate;
- pytest;
- FastAPI startup;
- PostgreSQL migrations.

Reason: current tool environment cannot install dependencies or run full repo checks.

## Required next validation in Codex/local runner

Run inside `backend_v2`:

```bash
python -m compileall app
pytest
alembic revision --autogenerate -m "init v2 schema"
```

If errors occur:

- fix only V2 files;
- keep legacy `api/`, `intaxi_bot/`, `src/` untouched;
- do not merge into main until these checks pass.

## Current merge policy

PR #2 / `v2-core-plan` remains a foundation branch.

Do not make V2 production-active until:

- migrations are generated and reviewed;
- city flow smoke test runs against DB;
- Mini App V2 calls Backend V2;
- Bot V2 calls Backend V2;
- admin panel can manage driver review, commission, payments and donation settings;
- legacy hotfix flows are disabled or replaced safely.
