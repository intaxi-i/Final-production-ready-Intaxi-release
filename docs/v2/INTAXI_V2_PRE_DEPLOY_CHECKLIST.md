# Intaxi V2 Pre-Deploy Checklist

This checklist defines the stage immediately before deploying V2 to the server.

## Backend V2 readiness

Implemented:

- FastAPI app
- async SQLAlchemy setup
- Alembic setup
- initial schema migration file
- city order/trip flow
- intercity request/route/trip scaffold
- user profile and role APIs
- driver profile submission
- vehicle submission
- driver online/location APIs
- driver payment methods
- wallet read/ledger/topup APIs
- admin driver review
- admin women-mode driver review
- admin payment review
- admin commission rules
- admin donation/support payment settings
- public active donation settings
- support tickets
- admin audit records for critical mutations

Still required before public launch:

- real Telegram WebApp/session auth
- admin seed/creation command
- encryption/protected storage for sensitive card and wallet values
- PostgreSQL integration smoke test on VPS
- endpoint HTTP smoke tests on VPS

## Mini App V2 readiness

Implemented:

- home navigation
- profile page
- city create page
- passenger my city orders page
- driver online page
- driver payment methods page
- available city offers page
- current trip page
- public support/donation settings page
- admin landing page
- admin driver review page
- admin payment review page
- admin commission page
- admin support payment settings page

Still required before public launch:

- Telegram WebApp init data auth
- production user/session handling
- real map picker
- real location permissions and provider selection
- visual polish and mobile QA

## Bot V2 readiness

Implemented:

- bot API client skeleton
- notification formatting skeleton
- Mini App deep-link helper

Still required before public launch:

- aiogram entrypoint
- Telegram WebApp auth/session handoff
- order/trip notifications from backend events
- admin quick actions through backend APIs

## Server deployment package

Implemented:

- backend_v2/.env.example
- backend_v2/Dockerfile
- backend_v2/docker-compose.yml
- miniapp_v2/.env.example
- miniapp_v2/Dockerfile
- deployment runbook

## Required VPS commands before merge/public launch

```bash
cd /opt/intaxi/repo/backend_v2
docker compose up -d --build
docker compose exec backend python -m compileall app
docker compose exec backend python -c "from app.main import app; print(app.title)"
docker compose exec backend python -c "from app.core.database import Base; from app import models; print(len(Base.metadata.tables)); print(sorted(Base.metadata.tables.keys()))"
docker compose exec backend alembic upgrade head
```

Mini App:

```bash
cd /opt/intaxi/repo/miniapp_v2
docker build -t intaxi-miniapp-v2 .
```

Public checks:

```bash
curl https://api.intaxi.best/health
curl https://api.intaxi.best/api/v2/public/donation-payment-settings
```

## Merge policy

Do not merge `v2-core-plan` into `main` until:

- VPS backend build passes;
- Alembic upgrade against real PostgreSQL passes;
- Mini App build passes;
- at least one city order/trip smoke flow is verified;
- dev auth is replaced or deployment is explicitly internal-only.
