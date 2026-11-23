#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
PORT="${BHAIJANLAL_BACKEND_PORT:-8790}"
echo "Starting Bhajanlal backend on 127.0.0.1:$PORT"
exec python3 "$DIR/backend.py"
