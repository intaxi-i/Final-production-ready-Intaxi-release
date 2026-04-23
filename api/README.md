# InTaxi API

FastAPI backend for Telegram Mini App authentication/session and profile endpoints.

## Endpoints

- `POST /auth/telegram`
- `POST /dev/session` (development/local only; disabled in production)
- `GET /me`
- `GET /wallet`
- `POST /me/profile`
- `POST /me/role`
- `POST /me/vehicle`

## Environment

- `BOT_TOKEN` (required for `/auth/telegram`)
- `SESSION_SECRET` (optional, reserved for future token signing)
- `DEV_TG_ID` (optional, default `89137224`)
- `DEV_FULL_NAME` (optional)
- `DEV_USERNAME` (optional)
- `DATABASE_URL` (optional; defaults to bot sqlite path via shared models)

## Run

```bash
cd /workspace/intaxi
python -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Notes

Reuses SQLAlchemy models and request helpers from `intaxi_bot.app.database`.

Uses in-memory bearer sessions (valid for 14 days).

Validates Telegram WebApp init data HMAC using `BOT_TOKEN`.
