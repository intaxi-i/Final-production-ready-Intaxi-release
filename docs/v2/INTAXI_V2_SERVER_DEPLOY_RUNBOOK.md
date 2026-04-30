# Intaxi V2 Server Deploy Runbook

Target server assumptions:

- Ubuntu 24.04 LTS
- Docker and Docker Compose installed
- Nginx installed
- UFW allows ports 22, 80, 443
- project base folder: `/opt/intaxi`
- API domain: `api.intaxi.best`

## 1. Prepare source on VPS

```bash
cd /opt/intaxi
git clone https://github.com/intaxi-i/Final-production-ready-Intaxi-release.git repo
cd /opt/intaxi/repo
git fetch origin
git checkout v2-core-plan
git pull origin v2-core-plan
```

## 2. Prepare Backend V2 env

```bash
cd /opt/intaxi/repo/backend_v2
cp .env.example .env
nano .env
```

Required values:

```text
APP_ENV=production
DATABASE_URL=postgresql+asyncpg://intaxi:CHANGE_DB_PASSWORD@postgres:5432/intaxi_v2
SESSION_SECRET=CHANGE_LONG_RANDOM_SECRET
BOT_TOKEN=TELEGRAM_BOT_TOKEN_WHEN_READY
CORS_ORIGINS=https://intaxi.best,https://www.intaxi.best,https://app.intaxi.best,https://api.intaxi.best
```

Before compose start:

```bash
export POSTGRES_PASSWORD='CHANGE_DB_PASSWORD'
```

## 3. Build and start Backend V2

```bash
cd /opt/intaxi/repo/backend_v2
docker compose up -d --build
docker compose ps
docker compose logs -f backend
```

Local health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected result:

```json
{"status":"ok","app":"Intaxi Backend V2"}
```

## 4. Nginx reverse proxy

Create `/etc/nginx/sites-available/api.intaxi.best` with reverse proxy to `127.0.0.1:8000`.

Required proxy headers:

```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

Then:

```bash
sudo ln -s /etc/nginx/sites-available/api.intaxi.best /etc/nginx/sites-enabled/api.intaxi.best || true
sudo nginx -t
sudo systemctl reload nginx
```

Public check:

```bash
curl http://api.intaxi.best/health
```

## 5. HTTPS

After DNS points to VPS, issue a certificate with your preferred ACME/certbot setup and re-check:

```bash
curl https://api.intaxi.best/health
```

## 6. Mini App V2 env

```bash
cd /opt/intaxi/repo/miniapp_v2
cp .env.example .env.local
nano .env.local
```

Required:

```text
NEXT_PUBLIC_INTAXI_API_BASE_URL=https://api.intaxi.best
```

`NEXT_PUBLIC_INTAXI_DEV_USER_TOKEN=dev:1` is development-only and must be replaced by real Telegram WebApp/session auth before public launch.

## 7. Mini App V2 build check

```bash
cd /opt/intaxi/repo/miniapp_v2
docker build -t intaxi-miniapp-v2 .
docker run --rm -p 127.0.0.1:3000:3000 intaxi-miniapp-v2
```

Then:

```bash
curl http://127.0.0.1:3000
```

## 8. Backend validation on VPS

```bash
cd /opt/intaxi/repo/backend_v2
docker compose exec backend python -m compileall app
docker compose exec backend python -c "from app.main import app; print(app.title)"
docker compose exec backend python -c "from app.core.database import Base; from app import models; print(len(Base.metadata.tables)); print(sorted(Base.metadata.tables.keys()))"
docker compose exec backend alembic upgrade head
```

## 9. Smoke checks

```bash
curl https://api.intaxi.best/health
curl https://api.intaxi.best/api/v2/public/donation-payment-settings
```

## 10. Current blockers before public launch

Do not announce public launch until:

- real Telegram WebApp auth/session replaces dev tokens;
- admin user creation/seed flow exists;
- PostgreSQL-backed integration smoke tests pass;
- payment setting secret storage is encrypted or otherwise protected;
- HTTPS is active;
- Cloudflare DNS for `api.intaxi.best` points to VPS;
- Mini App domain is configured in BotFather.

## 11. Safe rollback

```bash
cd /opt/intaxi/repo/backend_v2
docker compose logs backend --tail=200
docker compose down
```

Database volume remains preserved unless manually deleted.
