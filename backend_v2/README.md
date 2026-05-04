# Intaxi Backend V2

Clean backend core for Intaxi V2.

## Principles

- FastAPI application.
- PostgreSQL via SQLAlchemy async.
- Alembic migrations.
- Business logic lives in services.
- API, bot and Mini App must not duplicate business rules.
- Telegram bot is an adapter/client, not the business core.

## First target

City MVP V2:

1. passenger creates city order;
2. eligible driver sees/accepts/counteroffers;
3. city trip is created;
4. current trip works for passenger and driver;
5. driver updates valid statuses;
6. order/trip statuses stay synchronized;
7. wallet ledger is ready for commission when commission becomes non-zero.
