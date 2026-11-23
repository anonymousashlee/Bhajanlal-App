# Bhajanlal — Portable Build

Everything needed to run Bhajanlal on **any computer** is inside this one
folder. Copy the whole folder anywhere (pendrive, another PC) — no files are
left behind; every script resolves its own location at runtime.

## Use in OpenCode — public, no API key

Anyone in the world can add **Bhajanlal Pro Max 2.5 free** to their OpenCode.
No API key, no signup, cost is `0`. Pick it via `/models` after installing.

**One-liner install** (backs up your existing config, then installs ours —
skip the overwrite if you already have an `opencode.json` you care about):

```sh
mkdir -p ~/.config/opencode && cp ~/.config/opencode/opencode.json ~/.config/opencode/opencode.json.bak 2>/dev/null; curl -s http://YOUR_VPS_IP:8788/opencode.json -o ~/.config/opencode/opencode.json
```

> If you already have an `opencode.json`, don't overwrite it — just merge the
> `"model"` and `"providers"` keys from the manual block below into yours.

**Manual install** — paste this into `~/.config/opencode/opencode.json`
(merge the `providers` + `model` keys if you already have one):

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "bhajanlal/pro-max-2.5-free",
  "providers": {
    "bhajanlal": {
      "name": "Bhajanlal",
      "package": "@opencode/ai/providers/openai-compatible",
      "settings": {
        "baseURL": "http://YOUR_VPS_IP:8788/v1",
        "apiKey": ""
      },
      "models": {
        "pro-max-2.5-free": {
          "name": "Bhajanlal Pro Max 2.5 free",
          "modelID": "bhajanlal/pro-max-2.5-free",
          "reasoning": true,
          "interleaved": "reasoning_content",
          "limit": { "context": 1048576, "output": 131072 },
          "cost": { "input": 0, "output": 0, "cache": { "read": 0, "write": 0 } }
        }
      }
    }
  }
}
```

Then restart OpenCode and run `/models` → **Bhajanlal Pro Max 2.5 free**.

- Public endpoint (after VPS deploy, `deploy/FREE-VPS-GUIDE.md`): `http://YOUR_VPS_IP:8788` (`/health`, `/opencode.json`, `/v1/chat/completions`)
  - Local equivalent: `http://127.0.0.1:8788`; the old quick-tunnel URL died with the tunnel.
- Local endpoint: `http://localhost:8788/`
- Note: the quick-tunnel URL changes if the tunnel restarts — re-fetch
  `/opencode.json` from the new URL, or deploy a fixed domain (see
  `deploy/vps/README.md` and `deploy/FREE-VPS-GUIDE.md`).

## What's inside

```
Bhajanlal-App/
├── README-PORTABLE.md          ← this file
├── requirements.txt            ← Python dependencies
├── Bhajanlal-App-original.zip  ← original source archive (v1–v4 LoRA adapters,
│                                  used to rebuild the merged model if ever needed)
├── orchestrator.py             ← phase runner (library/foundation/evals/data/train/serve/selflearn)
├── config.json  state.json
├── serve/
│   ├── endpoint.py             ← OpenAI-compatible server (port 8788) + /v1/feedback
│   └── backend.py webui.html
├── train/
│   ├── checkpoints/bhajanlal-pro-max-2/   ← THE model (dense fp16, ~988 MB)
│   ├── infer.py                ← one-shot local inference
│   ├── merge_pro_max.py        ← rebuild recipe (needs adapters restored from the zip)
│   └── data*.jsonl train*.py   ← training data + scripts
├── evals/
│   ├── harness.py              ← real scorer: 18 golden cases, pass@1 vs 0.75 target
│   ├── golden/cases.jsonl
│   └── results/                ← archived run results
├── selflearn/                  ← Self-Learning Loop (harvest → verify → train → eval → promote)
│   └── harvest/feedback.jsonl  ← filled via POST /v1/feedback
├── deploy/                     ← VPS provisioning scripts (paths are script-relative now)
├── docs/  logs/
```

## Model

**bhajanlal-pro-max-2** — all four Bhajanlal fine-tunes (v1–v4) compiled into
one dense model over `Qwen/Qwen2.5-0.5B-Instruct` (v4-dominant weighted
SVD merge). It is fully self-contained: no HuggingFace download is needed
to run it. See `train/checkpoints/bhajanlal-pro-max-2/README.md`.

## Setup on a new PC

```bash
# 1. Python 3.9+ (3.10+ recommended)
python3 --version

# 2. Dependencies (~3 GB disk for torch)
python3 -m pip install -r requirements.txt

# 3. Run the server (auto-loads the local model on startup)
python3 serve/endpoint.py
```

Then:

```bash
curl http://127.0.0.1:8788/health
curl http://127.0.0.1:8788/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"bhajanlal/local","messages":[{"role":"user","content":"Write a Python function to reverse a string."}]}'
```

- `"model": "bhajanlal/local"` → pins the local bhajanlal-pro-max-2 checkpoint (works fully offline).
- Omitting it / other aliases → upstream free models (requires the `opencode`
  CLI installed and logged in; falls back to the local model automatically).

## Verify

```bash
python3 evals/harness.py --self-check   # validates the 18 golden cases
python3 evals/harness.py --run --local  # scores the local model (pass@1 vs 0.75)
python3 train/infer.py "your prompt"    # one-shot inference
```

## Self-learning loop

```bash
curl -X POST http://127.0.0.1:8788/v1/feedback -H 'Content-Type: application/json' \
  -d '{"session_id":"s1","signal":"thumbs_up","release":"bhajanlal-pro-max-2","timestamp":"2026-11-22T15:00:00","consent":true}'
curl http://127.0.0.1:8788/v1/feedback   # harvest count
```

Feedback lands in `selflearn/harvest/feedback.jsonl`; the loop's weekly
stages (harvest → verify → train → eval → promote) consume it once armed.

## Portability notes

- All runtime paths are **self-locating** (derived from the script's own
  location). Optional overrides: `BHAIJANLAL_HOME`, `BHAIJANLAL_MODEL_PATH`,
  `BHAIJANLAL_ENDPOINT`, `BHAIJANLAL_SECRET_PATH`.
- The base model cache (`~/.cache/huggingface`) is NOT required for
  inference — only for retraining (scripts will re-download
  `Qwen/Qwen2.5-0.5B-Instruct` if you retrain).
- GPU: runs on CPU (slow), Apple MPS, or CUDA — auto-detected.
- Rebuilding the merge: unzip `Bhajanlal-App-original.zip` and copy its
  `app/train/checkpoints/bhajanlal-v1..v4` folders back, then run
  `python3 train/merge_pro_max.py`.
