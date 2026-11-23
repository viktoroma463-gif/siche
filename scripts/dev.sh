#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

API_PORT="${SICHE_API_PORT:-8010}"
WEB_PORT="${SICHE_WEB_PORT:-5174}"

if [[ ! -d "$ROOT/.venv" ]]; then
  python3 -m venv "$ROOT/.venv"
fi
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"
pip install -q -r "$ROOT/backend/requirements.txt"

if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  (cd "$ROOT/frontend" && npm install)
fi

cleanup() {
  trap - EXIT
  if [[ -n "${API_PID:-}" ]]; then kill "$API_PID" 2>/dev/null || true; fi
  if [[ -n "${WEB_PID:-}" ]]; then kill "$WEB_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

export PYTHONPATH="$ROOT/backend"
echo "思拆 API  →  http://127.0.0.1:${API_PORT}/"
echo "思拆 界面 →  http://127.0.0.1:${WEB_PORT}/"
uvicorn app.main:app --app-dir "$ROOT/backend" --host 127.0.0.1 --port "$API_PORT" &
API_PID=$!
(cd "$ROOT/frontend" && npm run dev -- --host 127.0.0.1 --port "$WEB_PORT") &
WEB_PID=$!
wait
