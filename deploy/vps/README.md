# Deploy Bhajanlal endpoint to a VPS (public, 24/7)

This gives you a stable public URL with no laptop dependency.

## 1. Provision a VPS
Any Linux VPS works. Recommended: **Hetzner CPX11 (€4.5/mo, 2 vCPU, 4GB RAM)** or **DigitalOcean $6/mo**. For GPU (faster inference), use a GPU instance (~$0.5-1/hr).

## 2. On the VPS
```bash
# Upload the bundle
scp -r deploy/vps root@YOUR_VPS_IP:/tmp/bhajanlal-deploy
ssh root@YOUR_VPS_IP
bash /tmp/bhajanlal-deploy/setup.sh

# Copy endpoint + model from your Mac
# (run these from your Mac)
# (run from the Bhajanlal-App repo root)
scp serve/endpoint.py root@YOUR_VPS_IP:/opt/bhajanlal/serve/
rsync -av train/checkpoints/bhajanlal-pro-max-2/ root@YOUR_VPS_IP:/opt/bhajanlal/model/

# On VPS: point model path + start
ssh root@YOUR_VPS_IP 'sed -i "s#BHAIJANLAL_MODEL_PATH.*#BHAIJANLAL_MODEL_PATH=/opt/bhajanlal/model#" /etc/systemd/system/bhajanlal-endpoint.service; systemctl start bhajanlal-endpoint; systemctl status bhajanlal-endpoint'
```

## 3. Test
```bash
curl http://YOUR_VPS_IP:8788/health
curl -H "Authorization: Bearer bhajanlal" -X POST http://YOUR_VPS_IP:8788/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"bhajanlal/flash","messages":[{"role":"user","content":"hi"}],"stream":false}'
```

## 4. (Optional) HTTPS with a domain
Install Caddy on the VPS:
```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install caddy
```
Then `/etc/caddy/Caddyfile`:
```
bhajanlal.yourdomain.com {
    reverse_proxy localhost:8788
}
```
`systemctl reload caddy` → now accessible at `https://bhajanlal.yourdomain.com`.

## 5. Point OpenCode (on any computer) to the VPS
In `~/.config/opencode/opencode.json`:
```json
"baseURL": "http://YOUR_VPS_IP:8788/v1"   (or https://bhajanlal.yourdomain.com/v1)
```

## Notes
- CPU inference on a 2-vCPU VPS: ~15-30s per response for the 0.5B model. For faster, use a GPU VPS or set a paid provider via `BHAIJANLAL_PAID_BASE_URL`/`BHAIJANLAL_PAID_API_KEY`.
- The self-learning loop and auto-build stay on your Mac (they read the local OpenCode DB). The VPS only serves inference.
- For a stable public URL without a domain, the cloudflared tunnel on your Mac (already set up) works but requires the Mac to stay on.
