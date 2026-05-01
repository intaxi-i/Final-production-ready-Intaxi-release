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
- protected value helper

Mini App V2 includes:

- profile
- city create
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
curl http://127.0.0.1:8000/health
```

Mini App build:

```bash
cd /opt/intaxi/repo/miniapp_v2
docker build -t intaxi-miniapp-v2 .
```

## Important unresolved items

The GitHub connector blocked direct edits to the main backend auth dependency and main Mini App API client auth header. Because of that:

- Telegram initData verification helper exists.
- Telegram Mini App helper exists.
- Final dependency swap still must be applied in backend route auth.
- Main Mini App API client still needs to send Telegram initData to backend for all authenticated requests.

## Public launch status

Ready for server trial: yes.

Ready for public launch: no.

Before public launch:

1. Apply final Telegram auth dependency swap.
2. Wire protected value helper into all payment setting writes.
3. Run PostgreSQL Alembic upgrade on VPS.
4. Run Mini App Docker build.
5. Enable HTTPS for api.intaxi.best.
6. Verify one full city flow on real PostgreSQL.
