#!/usr/bin/env bash
# Provision a free AWS t3.micro (12 months) or t3.small and deploy Bhajanlal.
# Requires: AWS CLI + login with free-tier account.
set -euo pipefail

RG_NAME=bhajanlal-rg
REGION=us-east-1
VM_NAME=bhajanlal
SIZE="${AWS_INSTANCE_TYPE:-t3.micro}"   # 1GB RAM, 12-month free tier
IMAGE=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-arm64-server-20240621.001    # t3.micro ARM (newer)
# fallback x64: Ubuntu2204
KEY_NAME="${AWS_KEY_NAME:-bhajanlal-key}"
DEPLOY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/deploy-to-vps.sh"
AZ="$MAC_HOME/.local/azvenv/bin/az"   # shared azvenv; override with $PATH az

echo "==> Checking AWS CLI"
if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI not found. Installing..."
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -q /tmp/awscliv2.zip -d /tmp/aws
  sudo /tmp/aws/install
fi
AWS="$(command -v aws)"

echo "==> Logging in to AWS"
"$AWS" sts get-caller-identity >/dev/null 2>&1 || {
  echo "Not logged in. Running aws configure..."
  "$AWS" configure    # prompts for AWS_ACCESS_KEY_ID, secret, region, output
}

echo "==> Checking for existing key pair"
if ! "$AWS" ec2 describe-key-pairs --key-names "$KEY_NAME" >/dev/null 2>&1; then
  echo "Creating key pair: $KEY_NAME"
  "$AWS" ec2 create-key-pair --key-name "$KEY_NAME" --query 'KeyMaterial' --output text > "$HOME/.ssh/${KEY_NAME}.pem"
  chmod 400 "$HOME/.ssh/${KEY_NAME}.pem"
  echo "Saved to $HOME/.ssh/${KEY_NAME}.pem  (keep this safe!)"
else
  echo "Key pair already exists."
fi

IP=$("$AWS" ec2 describe-instances \
  --filters "Name=tag:Name,Values=$VM_NAME" "Name=instance-state-code,Values=16" \
  --query "Reservations[].Instances[].PublicIpAddress" -o tsv 2>/dev/null)

if [ -z "$IP" ]; then
  echo "==> Launching EC2 $VM_NAME ($SIZE, $IMAGE)"
  IN=$("$AWS" ec2 run-instances \
    --instance-type "$SIZE" \
    --image-id "$IMAGE" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$VM_NAME}]" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$("$AWS" ec2 describe-security-groups --filters "Name=vpc-id,Values=$( $AWS ec2 describe-vpcs --query 'Vpcs[0].VpcId' -o tsv)" --query 'GroupId' -o tsv)" \
    --subnet-id "$("$AWS" ec2 describe-subnets --filters "Name=vpc-id,Values=$( $AWS ec2 describe-vpcs --query 'Vpcs[0].VpcId' -o tsv)" --query 'Subnets[0].SubnetId' -o tsv)" \
    --associate-public-ip-address \
    --query "Instances[0].PublicIpAddress" -o tsv)
  IP=$IN
  sleep 5
  echo "Instance launched, IP=$IP"
else
  echo "Instance already running, IP=$IP"
fi

# open port 8788
echo "==> Opening port 8788"
"$AWS" ec2 authorize-security-group-ingress \
  --group-id "$("$AWS" ec2 describe-security-groups --filters "Name=vpc-id,Values=$( $AWS ec2 describe-vpcs --query 'Vpcs[0].VpcId' -o tsv)" --query 'GroupId' -o tsv)" \
  --protocol tcp --port 8788 --cidr 0.0.0.0/0 >/dev/null 2>&1 || true

echo "==> Deploying..."
# Use SSH -i form so the deploy script works with AWS .pem keys
SSH_OPTS="-i $HOME/.ssh/${KEY_NAME}.pem"
export SSH_OPTS
export AWS_INSTANCE_IP="$IP"

"$DEPLOY" "ubuntu@$IP"

echo
echo "==> Done. Health check:"
echo "    curl http://$IP:8788/health"
echo "==> Public URL for any OpenCode user:"
echo "    baseURL: http://$IP:8788/v1"
echo "    apiKey: bhajanlal"
echo
echo "Notes"
echo "--------"
echo "• t3.micro = 1GB RAM → model auto-runs int8 (bitsandbytes) via BHAIJANLAL_QUANT=auto."
echo "• First run takes ~5-8 min (pip installs torch + bitsandbytes)."
echo "• After 12 months, the instance stops being free. Stop it or upgrade."
echo "• If you later want faster: add BHAIJANLAL_PAID_BASE_URL + KEY on the VPS."
echo "• To stop and save:  aws ec2 stop-instances --instance-ids $IP"