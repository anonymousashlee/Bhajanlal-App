#!/usr/bin/env bash
# Provision a free Azure VM and deploy Bhajanlal. Requires `az login` first.
set -euo pipefail

RG=bhajanlal-rg
LOC="${AZURE_LOCATION:-eastus}"
NAME=bhajanlal
SIZE="${AZURE_SIZE:-Standard_D2s_v3}"   # 2 vCPU / 8GB (fits $200 free credit)
IMAGE=Ubuntu2204
SSHKEY="${SSH_PUB_KEY:-$HOME/.ssh/id_ed25519.pub}"
DEPLOY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/deploy-to-vps.sh"

# locate az (venv install or system)
AZ=""
for c in "$MAC_HOME/.local/azvenv/bin/az" "/tmp/scratchpad/azvenv/bin/az" "$(command -v az 2>/dev/null || true)"; do
  [ -n "$c" ] && [ -x "$c" ] && AZ="$c" && break
done
[ -z "$AZ" ] && { echo "az CLI not found (still installing?)"; exit 1; }

echo "==> Checking Azure login"
"$AZ" account show >/dev/null 2>&1 || { echo "NOT LOGGED IN. Run:  $AZ login"; exit 1; }

echo "==> Creating resource group $RG in $LOC"
"$AZ" group create --name "$RG" --location "$LOC" --output none

echo "==> Creating VM $NAME ($SIZE, $IMAGE)"
"$AZ" vm create \
  --resource-group "$RG" \
  --name "$NAME" \
  --image "$IMAGE" \
  --size "$SIZE" \
  --admin-username azureuser \
  --ssh-key-values "$SSHKEY" \
  --public-ip-sku Standard \
  --nsg-rule SSH \
  --output none

echo "==> Opening port 8788"
"$AZ" vm open-port --resource-group "$RG" --name "$NAME" --port 8788 --priority 1001 --output none

IP=$("$AZ" vm list-ip-addresses --resource-group "$RG" --name "$NAME" --query "virtualMachine.network.publicIpAddresses[0].ipAddress" -o tsv)
echo "==> Public IP: $IP"
echo "==> Deploying..."
"$DEPLOY" "azureuser@$IP"
echo "==> Done. Health: curl http://$IP:8788/health"
