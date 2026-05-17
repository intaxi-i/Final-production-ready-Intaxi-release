#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "== Python version =="
"$PYTHON_BIN" --version

echo "== Compile Python packages =="
"$PYTHON_BIN" -m compileall -q api intaxi_bot

echo "== Import API and bot modules =="
"$PYTHON_BIN" - <<'PY'
import api.main
print('api.main import ok')
import intaxi_bot.main
print('intaxi_bot.main import ok')
PY

echo "== Check critical API routes =="
"$PYTHON_BIN" - <<'PY'
import api.main

required = {
    ('POST', '/me/profile'),
    ('POST', '/me/role'),
    ('POST', '/me/vehicle'),
    ('POST', '/driver/online'),
    ('POST', '/city/orders/{order_id}/close'),
    ('GET', '/city/offers'),
    ('GET', '/city/orders/available'),
    ('POST', '/city/offers/{order_id}/accept'),
    ('POST', '/city/orders/{order_id}/accept'),
    ('POST', '/city/trips/{trip_id}/status'),
    ('GET', '/trip/current'),
    ('GET', '/history/all'),
    ('GET', '/intercity/offers'),
    ('GET', '/intercity/offers/search'),
    ('GET', '/intercity/offers/{kind}/{item_id}'),
    ('POST', '/intercity/offers/{kind}/{item_id}/accept'),
    ('POST', '/intercity/routes/{route_id}/status'),
    ('POST', '/intercity/requests/{request_id}/status'),
}

registered = set()
for route in api.main.app.router.routes:
    path = getattr(route, 'path', None)
    methods = getattr(route, 'methods', None) or []
    for method in methods:
        registered.add((method.upper(), path))

missing = sorted(required - registered)
if missing:
    print('Missing routes:')
    for method, path in missing:
        print(f'{method} {path}')
    raise SystemExit(1)

for method, path in sorted(required):
    print(f'ok {method} {path}')
PY

echo "== Predeploy smoke check passed =="
