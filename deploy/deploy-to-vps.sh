#!/usr/bin/env bash
# One-command VPS deployment for Bhajanlal endpoint.
# Usage:
#   ./deploy-to-vps.sh root@1.2.3.4
#   ./deploy-to-vps.sh ubuntu@1.2.3.4 ~/Downloads/bhajanlal.pem     (AWS key)
#   SSH_OPTS="-i ~/.ssh/id_ed25519" ./deploy-to-vps.sh ubuntu@1.2.3.4
set -euo pipefail

TARGET="${1:?Usage: ./deploy-to-vps.sh <user@vps-ip> [ssh-key.pem]}"
SSH_KEY="${2:-}"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SSH_OPTS="${SSH_OPTS:-}"
RSYNC_RSH="ssh"
if [ -n "$SSH_KEY" ]; then
  chmod 400 "$SSH_KEY" 2>/dev/null || true
  SSH_OPTS="$SSH_OPTS -i $SSH_KEY"
  RSYNC_RSH="ssh -i $SSH_KEY"
fi
# shellcheck disable=SC2086
SSHCMD() { ssh $SSH_OPTS "$@"; }
SCPCMD() { scp $SSH_OPTS "$@"; }

echo "==> Testing SSH connection to $TARGET"
SSHCMD -o ConnectTimeout=10 -o BatchMode=yes "$TARGET" 'echo connected' >/dev/null || {
  echo "SSH failed. Check: key file correct? port 22 open? user right (ubuntu/azureuser/root)?"
  exit 1
}

echo "==> Uploading bundle to $TARGET"
SSHCMD "$TARGET" 'mkdir -p /tmp/bhajanlal-deploy'
SCPCMD "$APP_DIR/deploy/vps/setup.sh" "$TARGET:/tmp/bhajanlal-deploy/"
SCPCMD "$APP_DIR/serve/endpoint.py" "$TARGET:/tmp/bhajanlal-deploy/"
echo "==> Uploading model checkpoint (~950MB)"
rsync -az -e "$RSYNC_RSH" --info=progress2 \
  "$APP_DIR/train/checkpoints/bhajanlal-pro-max-2/" "$TARGET:/tmp/bhajanlal-deploy/model/"

echo "==> Running setup + start on VPS (installs torch/transformers/bitsandbytes, enables swap)"
SSHCMD "$TARGET" 'bash /tmp/bhajanlal-deploy/setup.sh'

IP="${TARGET##*@}"
echo
echo "==> Done. Test with:"
echo "    curl http://$IP:8788/health"
echo "    curl -H \"Authorization: Bearer bhajanlal\" -X POST http://$IP:8788/v1/chat/completions -H 'Content-Type: application/json' -d '{\"model\":\"bhajanlal/flash\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"stream\":false}'"
