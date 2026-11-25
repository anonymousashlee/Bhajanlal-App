#!/usr/bin/env bash
# Bhajanlal-App one-click setup: auto-detects hardware and installs deps.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=== Bhajanlal-App setup ==="
PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then echo "python3 not found"; exit 1; fi
echo "python: $PY ($($PY --version))"

# Detect accelerator
ACCEL="none"
if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then
  ACCEL="cuda"
elif [ "$(uname)" = "Darwin" ] && [ "$(uname -m)" = "arm64" ]; then
  ACCEL="mps"
fi
echo "accelerator: $ACCEL"

# Install Python deps
if [ -f requirements.txt ]; then
  "$PY" -m pip install --upgrade pip >/dev/null 2>&1 || true
  "$PY" -m pip install -r requirements.txt
fi
if [ -f requirements-api.txt ]; then
  "$PY" -m pip install -r requirements-api.txt
fi

# MPS/CUDA-specific torch (only if missing)
if ! "$PY" -c "import torch" >/dev/null 2>&1; then
  case "$ACCEL" in
    cuda) "$PY" -m pip install torch --index-url https://download.pytorch.org/whl/cu121 ;;
    mps)  "$PY" -m pip install torch ;;
    *)    "$PY" -m pip install torch --index-url https://download.pytorch.org/whl/cpu ;;
  esac
fi

echo "=== setup complete (accelerator=$ACCEL) ==="
echo "Next: python3 orchestrator.py"
echo "       python3 orchestrator.py --dry-run   # preview"
echo "       python3 orchestrator.py --status     # current status"
