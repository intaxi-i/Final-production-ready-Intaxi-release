# API router split checklist

This directory is the target structure for moving the current monolithic FastAPI routes out of `api/main.py`.

## Safety rules

- Move one route group at a time.
- Keep route paths and response shapes compatible with the Mini App contract.
- Do not keep duplicate route definitions in `api/main.py` and router modules.
- After every route group migration, run Python compile/import smoke checks and route inventory checks.

## Planned order

1. `/me`, `/me/profile`, `/me/role`, `/me/vehicle`
2. `/driver/online`, `/driver/location`
3. `/city/*`
4. `/trip/current` and trip status routes
5. `/intercity/*`
6. `/history/all`
7. wallet/admin/payment routes or hide unfinished UI

## Required smoke command

```bash
PYTHONPATH="$PWD:$PWD/intaxi_bot" BOT_TOKEN=123456:TEST_TOKEN_FOR_IMPORT_ONLY APP_ENV=test python - <<'PY'
from collections import Counter
from api.main import app

routes = [
    (tuple(sorted(route.methods or [])), route.path)
    for route in app.routes
    if hasattr(route, 'methods')
]

dupes = [item for item, count in Counter(routes).items() if count > 1]
if dupes:
    raise SystemExit(f'Duplicate routes: {dupes}')

print('api route inventory ok', len(routes))
PY
```
