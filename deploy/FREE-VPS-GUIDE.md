# Get a FREE VPS (Oracle Cloud Always Free)

Oracle Cloud gives 2 always-free ARM VMs (up to 4 OCPU / 24GB RAM) — more than enough for the 0.5B model on CPU.

## Steps (10 minutes, one-time)

1. **Sign up**: https://cloud.oracle.com/free — always-free tier, no cost after signup.
   (They may ask for a credit card for identity verification; you are NOT charged.)

2. **Create a VM**:
   - Menu → Compute → Instances → Create Instance
   - Name: `bhajanlal`
   - Image: **Canonical Ubuntu 22.04 (or 24.04) aarch64** (ARM)
   - Shape: **VM.Standard.A1.Flex** — set **1 OCPU, 4 GB RAM** (free)
   - SSH keys: paste the public key from your Mac (`cat ~/.ssh/id_ed25519.pub`; generate with `ssh-keygen` if missing)
   - Networking: let it create a public subnet; note the **Public IP address**
   - Click **Create**

3. **Test SSH from your Mac**:
   ```bash
   ssh ubuntu@YOUR_VPS_IP    # user is 'ubuntu' on Oracle Ubuntu images
   ```

4. **Run the deploy** (from your Mac):
   ```bash
   cd /path/to/Bhajanlal-App && ./deploy/deploy-to-vps.sh ubuntu@YOUR_VPS_IP
   ```

5. **Verify**:
   ```bash
   curl http://YOUR_VPS_IP:8788/health
   ```

## Notes
- Oracle images use user `ubuntu` (not `root`). The deploy script handles it.
- Free tier ARM VM: 4GB RAM is plenty for the 0.5B model (CPU inference ~15-30s/response).
- If you want FASTER: keep it free, or add `BHAIJANLAL_PAID_BASE_URL`/`KEY` env on the VPS to route to a paid model.
- After deploying, point any OpenCode user's `baseURL` to `http://YOUR_VPS_IP:8788/v1`.
