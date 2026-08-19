#!/usr/bin/env bash
# Run backend and frontend locally without Docker.
# Usage:
#   ./scripts/run-local.sh         # runs backend (background) + frontend (foreground)
#   ./scripts/run-local.sh --no-frontend

set -euo pipefail
NO_FRONTEND=0
if [[ ${1:-} == "--no-frontend" ]]; then
  NO_FRONTEND=1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
cd "$ROOT_DIR"

# find python
PY=python3
if ! command -v "$PY" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PY=python
  else
    echo "Python3 not found in PATH. Install Python 3.8+." >&2
    exit 1
  fi
fi

VENV_DIR=backend/.venv
if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating venv at $VENV_DIR"
  $PY -m venv "$VENV_DIR"
fi

VENV_PY="$VENV_DIR/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
  echo "Venv python not found at $VENV_PY" >&2
  exit 1
fi

echo "Installing backend requirements..."
"$VENV_PY" -m pip install --upgrade pip >/dev/null
"$VENV_PY" -m pip install -r backend/requirements.txt

# read NEIS_API_KEY from .env if exists
NEIS_API_KEY=""
if [[ -f .env ]]; then
  NEIS_API_KEY_LINE=$(grep -E '^\s*NEIS_API_KEY\s*=' .env || true)
  if [[ -n "$NEIS_API_KEY_LINE" ]]; then
    NEIS_API_KEY=${NEIS_API_KEY_LINE#*=}
    NEIS_API_KEY=$(echo "$NEIS_API_KEY" | sed -e 's/^\s*//' -e 's/\s*$//')
  fi
fi

# start backend in background
echo "Starting backend in background..."
if [[ -n "$NEIS_API_KEY" ]]; then
  NEIS_API_KEY="$NEIS_API_KEY" "$VENV_PY" -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
else
  "$VENV_PY" -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
fi
backend_pid=$!
sleep 1
echo "Backend PID: $backend_pid"

if [[ $NO_FRONTEND -eq 1 ]]; then
  echo "No frontend requested. Exiting after starting backend (PID: $backend_pid)."
  exit 0
fi

# frontend
if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found in PATH. Install Node.js to run the frontend locally." >&2
  exit 1
fi

cd frontend
if [[ ! -d node_modules ]]; then
  echo "Installing frontend dependencies..."
  npm install
fi

echo "Starting frontend dev server (foreground). Press Ctrl+C to stop."
npm run dev

# on exit, optionally kill backend
echo "Frontend exited. Killing backend (PID: $backend_pid)"
kill $backend_pid || true
