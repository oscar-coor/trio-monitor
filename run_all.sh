#!/usr/bin/env bash
set -euo pipefail

# Run both backend (FastAPI/Uvicorn) and frontend (React) together.
# - Creates/uses Python venv at .venv
# - Installs backend and frontend deps if missing
# - Starts backend on 0.0.0.0:8000 and frontend on http://localhost:3000
# - Proxy in frontend/package.json should point to http://localhost:8000

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# --- Python / Backend setup ---
PYTHON_BIN=${PYTHON_BIN:-python3}
UVICORN_HOST=${UVICORN_HOST:-0.0.0.0}
UVICORN_PORT=${UVICORN_PORT:-8000}
FRONTEND_HOST=${FRONTEND_HOST:-0.0.0.0}
FRONTEND_PORT=${FRONTEND_PORT:-3000}

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: '$PYTHON_BIN' not found. Set PYTHON_BIN or install Python 3." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  echo "[setup] Creating virtual env .venv"
  "$PYTHON_BIN" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# Upgrade pip quietly
python -m pip install -q -U pip

# Install backend deps if needed
if [ -f backend/requirements.txt ]; then
  echo "[setup] Installing backend requirements"
  python -m pip install -q -r backend/requirements.txt
fi

# --- Frontend setup ---
if [ -d frontend ]; then
  pushd frontend >/dev/null
  if [ -f package-lock.json ]; then
    if [ ! -d node_modules ]; then
      echo "[setup] Installing frontend deps (npm ci)"
      npm ci
    fi
  else
    if [ ! -d node_modules ]; then
      echo "[setup] Installing frontend deps (npm install)"
      npm install
    fi
  fi
  popd >/dev/null
fi

# --- Start processes ---
BACKEND_LOG=${BACKEND_LOG:-"backend_server.log"}
FRONTEND_LOG=${FRONTEND_LOG:-"frontend_server.log"}

# Ensure logs exist
: >"$BACKEND_LOG"
: >"$FRONTEND_LOG"

cleanup() {
  echo "\n[cleanup] Stopping services..."
  if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "${FRONTEND_PID:-}" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" || true
    wait "$FRONTEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

# Start backend (served from backend/)
(
  cd backend
  echo "[run] Backend: uvicorn app:app --host $UVICORN_HOST --port $UVICORN_PORT"
  python -m uvicorn app:app --host "$UVICORN_HOST" --port "$UVICORN_PORT" >>"$BACKEND_LOG" 2>&1
) &
BACKEND_PID=$!

# Start frontend (CRA). Prevent auto-open browser.
(
  export BROWSER=none
  # Ensure CRA binds to all interfaces for remote access
  export HOST="$FRONTEND_HOST"
  cd frontend
  echo "[run] Frontend: HOST=$FRONTEND_HOST npm start -- --port $FRONTEND_PORT"
  npm start -- --port "$FRONTEND_PORT" >>"$FRONTEND_LOG" 2>&1
) &
FRONTEND_PID=$!

sleep 1

echo ""
echo "========================================"
echo "Backend running on:  http://${UVICORN_HOST}:${UVICORN_PORT}"
echo "Frontend running on: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "Logs: $BACKEND_LOG | $FRONTEND_LOG"
echo "Press Ctrl+C to stop both."
echo "========================================"
echo ""

# Tail logs interactively (optional). Comment out if undesired.
# tail -f "$BACKEND_LOG" "$FRONTEND_LOG"

# Wait for either to exit
wait -n "$BACKEND_PID" "$FRONTEND_PID"
exit_code=$?

# Trigger cleanup via trap, then exit with the code of the first process to finish
exit "$exit_code"
