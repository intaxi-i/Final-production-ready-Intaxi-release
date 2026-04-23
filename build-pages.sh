#!/usr/bin/env bash
set -euo pipefail

# Cloudflare Pages builds run in a temporary clone, so trimming backend-only
# content here is safe and prevents Vercel/next-on-pages from detecting the
# Python API and failing on missing `uv`.
rm -rf api intaxi_bot driver_files secure_driver_files codex_assets .venv
find . -maxdepth 1 \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) -delete

npx @cloudflare/next-on-pages@1
