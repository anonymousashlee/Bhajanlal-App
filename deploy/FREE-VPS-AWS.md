# Get a FREE VPS on AWS (t3.micro, 12 months)

AWS Free Tier gives **750 hours/month of t3.micro (1 vCPU, 1GB RAM) free for 12 months**.
The 1GB RAM is tight, so we run the model in **int8 quantization** (~500MB) — the deploy
script sets this automatically.

## Steps (10 minutes, one-time)

1. **Create free account**: https://aws.amazon.com/free/
   - Credit card for verification (no charge for free tier).

2. **Launch a VM (EC2)**:
   - Console → **EC2** → **Launch instance**
   - Name: `bhajanlal`
   - AMI: **Ubuntu Server 22.04 LTS (Free tier eligible)**
   - Instance type: **t3.micro** (Free tier eligible)
   - Key pair: **Create new** → download `.pem` → save it
   - Network settings → **Edit** → **Add security group rule**: Type **Custom TCP**, Port **8788**, Source **Anywhere**
   - Storage: 8 GB (free)
   - **Launch instance**

3. **Get the Public IP** from the instance list.

4. **Convert your key + test SSH** (from your Mac):
   ```bash
   chmod 400 ~/Downloads/your-key.pem
   ssh -i ~/Downloads/your-key.pem ubuntu@YOUR_VPS_IP
   ```

5. **Deploy** (from your Mac — key is the 2nd argument):
   ```bash
   ~/.config/opencode/bhajanlal/deploy/deploy-to-vps.sh \
     ubuntu@YOUR_VPS_IP ~/Downloads/your-key.pem
   ```
   The script tests SSH, uploads endpoint + model (~350MB), installs
   torch/transformers/bitsandbytes, creates a 2G swapfile, and starts the
   systemd service. First run takes ~5-8 min (pip downloads).

6. **Verify**:
   ```bash
   curl http://YOUR_VPS_IP:8788/health
   ```

## Notes
- User is `ubuntu` (Ubuntu AMI). The deploy script handles non-root sudo.
- t3.micro is 1GB RAM → `setup.sh` creates a 2G swapfile and the endpoint auto-selects
  **8-bit quantization** (`BHAIJANLAL_QUANT=auto` → bitsandbytes). ~15-30s/response.
- Verify quantization on the box: `curl http://IP:8788/metrics` → `"local_quant": "8bit"`.
- Free for 12 months (750 hrs/month). After that, stop the instance or downgrade.
- Point any OpenCode user's `baseURL` to `http://YOUR_VPS_IP:8788/v1`, key `bhajanlal`.
