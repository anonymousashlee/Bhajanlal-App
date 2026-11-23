#!/usr/bin/env bash
# VPS deployment for Bhajanlal endpoint (CPU inference). Works on Ubuntu/Debian.
# Runs as a normal user with sudo (e.g. 'ubuntu' on Oracle Cloud).
set -euo pipefail

APP=/opt/bhajanlal
RUNUSER=$(logname 2>/dev/null || echo "${SUDO_USER:-$(whoami)}")
[ "$RUNUSER" = "root" ] && RUNUSER="${SUDO_USER:-ubuntu}"
PORT=8788

echo "[1/7] system packages"
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv curl git rsync

echo "[2/7] user + dirs"
id -u "$RUNUSER" >/dev/null 2>&1 || sudo useradd -m -s /bin/bash "$RUNUSER"
sudo mkdir -p "$APP/serve" "$APP/model"
# move staged files into place if present
if [ -f /tmp/bhajanlal-deploy/endpoint.py ]; then
  sudo cp /tmp/bhajanlal-deploy/endpoint.py "$APP/serve/"
fi
if [ -d /tmp/bhajanlal-deploy/model ]; then
  sudo rsync -a /tmp/bhajanlal-deploy/model/ "$APP/model/"
fi
sudo chown -R "$RUNUSER:$RUNUSER" "$APP"

echo "[3/7] python venv"
sudo -u "$RUNUSER" python3 -m venv "$APP/venv"
sudo -u "$RUNUSER" "$APP/venv/bin/pip" install --upgrade pip
sudo -u "$RUNUSER" "$APP/venv/bin/pip" install torch --index-url https://download.pytorch.org/whl/cpu
sudo -u "$RUNUSER" "$APP/venv/bin/pip" install transformers peft accelerate
sudo -u "$RUNUSER" "$APP/venv/bin/pip" install bitsandbytes || echo "  WARN: bitsandbytes failed (fp16 fallback will be used)"

echo "[4/7] swap (needed on 1-2GB instances)"
if [ ! -f /swapfile ] && [ "$(swapon --show | wc -l)" -eq 0 ]; then
  sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null
  sudo swapon /swapfile
  echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab >/dev/null
  echo "  2G swap enabled"
fi

echo "[5/7] model path check"
if [ ! -f "$APP/model/model.safetensors" ] && [ ! -f "$APP/model/adapter_model.safetensors" ] && [ ! -d "$APP/model/checkpoint-252" ]; then
  echo "  WARN: model checkpoint not found in $APP/model — inference will fail until it's uploaded."
fi

echo "[6/7] systemd service"
sudo tee /etc/systemd/system/bhajanlal-endpoint.service >/dev/null <<EOF
[Unit]
Description=Bhajanlal OpenAI-compatible endpoint
After=network.target

[Service]
Type=simple
User=$RUNUSER
WorkingDirectory=$APP
Environment=BHAIJANLAL_HOST=0.0.0.0
Environment=BHAIJANLAL_API_KEY=bhajanlal
Environment=BHAIJANLAL_MODEL_PATH=$APP/model
Environment=BHAIJANLAL_QUANT=auto
Environment=BHAIJANLAL_HOST_PORT=8788
Environment=PYTHONUNBUFFERED=1
ExecStart=$APP/venv/bin/python $APP/serve/endpoint.py
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable bhajanlal-endpoint

echo "[7/7] firewall (ufw, if active)"
sudo ufw allow $PORT/tcp 2>/dev/null || true

echo
echo "Done. Files staged from /tmp/bhajanlal-deploy. Starting service..."
sudo systemctl restart bhajanlal-endpoint
sleep 3
sudo systemctl status bhajanlal-endpoint --no-pager | head -5
echo
echo "Test:  curl http://VPS_IP:$PORT/health"
echo "Public URL: http://VPS_IP:$PORT  (put behind Caddy for HTTPS)"
