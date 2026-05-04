# Intaxi V2 Local Validation Report

Validation was performed locally from the V2 source tree.

## Commands run

```bash
cd backend_v2
python -m compileall app
python -c "from app.main import app; print(app.title)"
python -c "from app.core.database import Base; from app import models; print(len(Base.metadata.tables)); print(sorted(Base.metadata.tables.keys()))"
pytest -q
alembic revision --autogenerate -m "init v2 schema"
```

## Results

Compile result: passed.

FastAPI app import result: passed.

Output:

```text
Intaxi Backend V2
```

SQLAlchemy metadata import result: passed.

Registered tables count:

```text
22
```

Registered tables:

```text
admin_audit_logs_v2
cities_v2
city_counteroffers_v2
city_orders_v2
city_trips_v2
commission_rules_v2
countries_v2
domain_events_v2
donation_payment_settings_v2
driver_online_states_v2
driver_payment_methods_v2
driver_profiles_v2
intercity_requests_v2
intercity_routes_v2
intercity_trips_v2
payment_topup_requests_v2
ratings_v2
support_tickets_v2
users_v2
vehicles_v2
wallet_ledger_entries_v2
wallets_v2
```

Pytest result:

```text
9 passed
```

Alembic autogenerate result: blocked by missing local PostgreSQL server.

Error summary:

```text
Connect call failed on localhost:5432
```

This was an environment limitation, not a Python import or SQLAlchemy metadata failure.

## Files added after validation

```text
backend_v2/alembic/versions/0001_init_v2_schema.py
backend_v2/tests/test_metadata_smoke.py
```

## Current backend_v2 status

Validated:

- Python compile
- FastAPI app import
- SQLAlchemy metadata import
- expected table registration
- city status transition tests
- pricing smoke tests
- commission smoke tests
- donation settings are separate from driver payment methods

Remaining production checks:

- run Alembic against real PostgreSQL
- run API integration tests with PostgreSQL
- verify FastAPI endpoints through HTTP client
- add real Telegram WebApp/session auth
- add stronger protected storage for sensitive payment setting values

## Readiness for next stage

Backend V2 foundation is ready to proceed to Mini App V2 implementation against `/api/v2`, while keeping the PR unmerged until PostgreSQL-backed Alembic/API checks pass.
