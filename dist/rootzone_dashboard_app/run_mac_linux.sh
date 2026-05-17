#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8765}"
URL="http://${HOST}:${PORT}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found. Install Python 3.11 or newer, then run this file again."
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "Creating local Python environment..."
  python3 -m venv .venv
fi

echo "Installing/updating required packages..."
".venv/bin/python" -m pip install --upgrade pip
".venv/bin/python" -m pip install -r requirements.txt

if command -v open >/dev/null 2>&1; then
  open "$URL" >/dev/null 2>&1 || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 || true
fi

echo "Rootzone dashboard is running at $URL"
echo "Keep this terminal open while using the dashboard. Press Ctrl+C to stop it."
exec ".venv/bin/python" rootzone_web_app.py --host "$HOST" --port "$PORT"
