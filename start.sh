#!/usr/bin/env bash
# Bootstrap and run the backend API (FastAPI) and frontend (Vite) together.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

python_bin() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
  else
    command -v python
  fi
}

PYTHON="$(python_bin)"

if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON" -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -e "$ROOT_DIR/backend"

pushd "$ROOT_DIR/backend" >/dev/null
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
popd >/dev/null

echo "Backend API started on http://localhost:8000"

tail_frontend() {
  pushd "$ROOT_DIR/frontend" >/dev/null
  npm install
  npm run dev -- --host --port 5173
  popd >/dev/null
}

tail_frontend &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

echo "Frontend dev server starting on http://localhost:5173 (proxy to backend as configured in Vite)."

# Wait for either process to exit
wait -n
