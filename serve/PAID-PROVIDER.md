# Bhajanlal - Paid Provider (for mimo-like quality + speed)

Free upstreams are rate-limited; configure a paid provider for consistent quality.

Setup (env vars):
  export BHAIJANLAL_PAID_BASE_URL="https://api.openai.com/v1"
  export BHAIJANLAL_PAID_API_KEY="sk-..."
  export BHAIJANLAL_PAID_MODEL="gpt-4o-mini"

Restart: launchctl kickstart -k gui/$(id -u)/com.bhajanlal.endpoint

Verify: curl -s http://127.0.0.1:8788/metrics

Local fallback uses checkpoint bhajanlal-v4 (v5 after retraining via train/train_v5.py).
