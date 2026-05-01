# Intaxi V2 Pre-Deploy Checklist

This checklist defines the stage immediately before deploying V2 to the server.

## Backend V2 readiness

Implemented:

- FastAPI app
- async SQLAlchemy setup
- Alembic setup
- initial schema migration file
- idempotent city order comment migration
- city order/trip flow
- intercity request/route/trip scaffold
- user profile and role APIs
- Telegram WebApp initData verification wired into auth dependency
- development auth disabled in production
- driver profile submission
- vehicle submission
- driver online/location APIs
- driver payment methods
- Fernet-protected driver card storage
- wallet read/ledger/topup APIs
- admin driver review
- admin women-mode driver review
- admin payment review
- admin commission rules
- admin donation/support payment settings
- Fernet-protected support/donation card and digital asset storage
- public active donation settings
- support tickets
- admin audit records for critical mutations
- admin seed/creation command
- tests for Telegram auth and protected values

Still required before public launch:

- PostgreSQL integration smoke test on VPS
- endpoint HTTP smoke tests on VPS
- full city flow verification against real PostgreSQL
- rotate all production secrets before public traffic

## Mini App V2 readiness

Implemented:

- polished home navigation
- PageHeader and BottomNav ported from legacy
- compact ru/uz/kz/en i18n layer
- Telegram WebApp bootstrap
- authenticated API clients using X-Telegram-Init-Data with dev fallback only outside production
- profile page
- stronger city create UX: waiting state, polling, driversSeen, raise-price flow, comment submission
- address field with current geolocation and manual coordinates
- Leaflet map point picker for pickup/destination
- reverse geocoding and coordinate payload submission
- compact country/region/city location directories
- passenger my city orders page
- driver online page
- driver registration page
- driver payment methods page
- available city offers page
- current trip page
- account/balance page
- support page
- public support/donation settings page
- admin landing page
- admin driver review page
- admin payment review page
- admin commission page
- admin support payment settings page

Still required before public launch:

- expand location directories to full production coverage for all target countries
- mobile QA on Telegram WebApp, including location permission prompts
- Mini App Docker build on VPS/CI

## Bot V2 readiness

Implemented:

- aiogram entrypoint skeleton
- bot API client skeleton
- notification formatting skeleton
- Mini App deep-link helper

Still required before public launch:

- backend event-driven order/trip notifications
- production webhook/polling decision
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
docker compose exec backend python -m app.cli.check_backend
docker compose exec backend alembic upgrade head
docker compose exec backend pytest
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
- backend pytest passes in container or CI;
- Mini App build passes;
- at least one city order/trip smoke flow is verified;
- HTTPS for api.intaxi.best is active;
- production secrets are rotated and dev tokens are not set in production.
