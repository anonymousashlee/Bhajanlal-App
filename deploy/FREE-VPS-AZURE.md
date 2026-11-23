# Get a FREE VPS on Azure

Azure free account gives **$200 credit for 30 days** + 12 months of free B1s VMs.
For the 0.5B model we need ~2GB RAM, so use the **credit** for a D2s_v3-class VM
(2 vCPU / 8GB) — that runs the whole month for free, then either keep a small
always-free B1s (with a lighter config) or let it stop.

## Steps (10 minutes, one-time)

1. **Create free account**: https://azure.microsoft.com/free/
   - Microsoft account required; credit card for verification only (no charge).
   - You get $200 credit valid 30 days.

2. **Create a VM** (portal):
   - Search **Virtual machines** → **Create** → **Virtual machine**
   - **Subscription**: Free Trial
   - **Resource group**: create `bhajanlal-rg`
   - **VM name**: `bhajanlal`
   - **Region**: `East US` or `West Europe` (choose nearest to you)
   - **Image**: **Ubuntu Server 22.04 LTS - x64 Gen 2**
   - **Size**: **Standard_D2s_v3** (2 vCPU / 8GB) — fits free credit
     (or **Standard_B1s** for always-free, but only 1GB RAM)
   - **Administrator account**: username `azureuser`, SSH public key
     (paste from your Mac: `cat ~/.ssh/id_ed25519.pub`)
   - **Inbound ports**: allow **SSH (22)** and **HTTP (80)** / **Custom 8788**
   - **Review + create** → **Create**

3. **Test SSH**:
   ```bash
   ssh azureuser@YOUR_VPS_IP
   ```

4. **Run the deploy** (from your Mac):
   ```bash
   ~/.config/opencode/bhajanlal/deploy/deploy-to-vps.sh azureuser@YOUR_VPS_IP
   ```

5. **Verify**:
   ```bash
   curl http://YOUR_VPS_IP:8788/health
   ```

## Notes
- User is `azureuser` (the deploy script handles non-root sudo automatically).
- D2s_v3 on the $200 credit: CPU inference ~8-15s/response (better than Oracle's 4GB).
- After 30 days, switch to a **Standard_B1s** (always-free 12 months) or stop the VM.
- Point any OpenCode user's `baseURL` to `http://YOUR_VPS_IP:8788/v1`.
- For HTTPS later, install Caddy/nginx on the VM (see vps/README.md).
