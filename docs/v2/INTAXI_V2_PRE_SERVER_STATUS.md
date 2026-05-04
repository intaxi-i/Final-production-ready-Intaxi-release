# Intaxi V2 Pre-Server Status

## Done in V2 branch

V2 remains isolated under:

- backend_v2/
- miniapp_v2/
- bot_v2/
- docs/v2/

Backend V2 includes:

- FastAPI app
- async SQLAlchemy models
- Alembic setup and initial migration
- user profile and roles
- city order/trip flow
- intercity scaffold
- driver profile submission
- vehicle submission
- driver online/location
- driver payment methods
- account balance/topup flow
- admin driver review
- admin payment review
- admin commission rules
- admin support payment settings
- public support payment settings
- support tickets
- admin audit service
- Dockerfile and docker-compose
- admin seed command
- backend metadata check command
- Telegram WebApp initData verification helper
- Telegram WebApp auth wired into backend dependency
- development auth disabled in production
- Fernet-based protected value helper
- protected writes for driver card values
- protected writes for support/donation card and digital asset values
- tests for Telegram auth verification
- tests for protected values

Mini App V2 includes:

- profile
- stronger city create UX ported from legacy: waiting state, polling, driversSeen, raise-price flow
- city my orders
- city offers
- current trip
- driver online
- driver registration
- driver vehicle submission
- driver payment methods
- account page
- support page
- public support payment page
- admin drivers
- admin payments
- admin commission
- admin support payment settings
- Telegram WebApp helper
- authenticated API clients using X-Telegram-Init-Data with dev fallback only outside production
- PageHeader and BottomNav UX ported from legacy
- compact ru/uz/kz/en i18n layer for V2 screens

Bot V2 includes:

- aiogram entrypoint skeleton
- API client skeleton
- notification formatter
- Mini App deep-link helper

## Commands added

Admin seed:

```bash
cd backend_v2
python -m app.cli.seed_admin --tg-id YOUR_TELEGRAM_ID --full-name "Intaxi Admin"
```

Backend metadata check:

```bash
cd backend_v2
python -m app.cli.check_backend
```

Backend test run:

```bash
cd backend_v2
pytest
```

## Server run requirements

Run on VPS:

```bash
cd /opt/intaxi/repo
git fetch origin
git checkout v2-core-plan
git pull origin v2-core-plan
cd backend_v2
cp .env.example .env
docker compose up -d --build
docker compose exec backend python -m compileall app
docker compose exec backend python -m app.cli.check_backend
docker compose exec backend alembic upgrade head
docker compose exec backend pytest
curl http://127.0.0.1:8000/health
```

Mini App build:

```bash
cd /opt/intaxi/repo/miniapp_v2
docker build -t intaxi-miniapp-v2 .
```

## Still required on VPS / CI

These items cannot be honestly marked complete until they are run on the actual server or CI:

- PostgreSQL Alembic upgrade against the real VPS database
- backend pytest run inside the backend container
- Mini App Docker build
- HTTPS through Nginx/Cloudflare for api.intaxi.best
- one full city smoke flow against the real database

## Public launch status

Ready for server trial: yes.

Ready for public launch: not yet.

Before public launch:

1. Run PostgreSQL Alembic upgrade on VPS.
2. Run backend tests on VPS/CI.
3. Run Mini App Docker build.
4. Enable HTTPS for api.intaxi.best.
5. Verify one full city flow on real PostgreSQL.
6. Replace any development test data and rotate secrets before exposing public traffic.
