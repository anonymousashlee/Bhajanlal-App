# Bhajanlal — Shell Command Reference

Format used throughout: **Thinking** first (the *why*), then the exact
`$ command` (the *what*) — reason, then execute. Every command below matches
this repo on macOS (Apple Silicon).

## Port map — know this first

| Port | Service | Auth | Launchd label |
|------|---------|------|---------------|
| 8788 | `serve/endpoint.py` — OpenAI-compatible endpoint | none (local) | `com.bhajanlal.endpoint` |
| 8790 | proxy backend OpenCode talks to | `Bearer bhajanlal-local` | `com.bhajanlal.proxy` |
| 8080 | `model-ops/proxy.py` — public auth proxy (loopback only) | `Bearer <secret>` | feeds the managed tunnel |

---

## 1. Is the stack healthy?

**Thinking:** Check 8788 first — if the endpoint is down, evals, feedback and
the one-liner all fail; then check 8790, which is what OpenCode actually
talks to.

```bash
$ curl -s http://127.0.0.1:8788/health
$ curl -s -o /dev/null -w '%{http_code}\n' -H 'Authorization: Bearer bhajanlal-local' http://127.0.0.1:8790/v1/models
```

Expected: `{"status":"ok","service":"bhajanlal-endpoint"}` then `200`.

---

## 2. Relaunch the app (both services)

**Thinking:** `kickstart -k` kills and restarts in one call — cleaner than a
stop/start pair. Verify both ports come back before touching anything else.

```bash
$ launchctl kickstart -k gui/$(id -u)/com.bhajanlal.endpoint
$ launchctl kickstart -k gui/$(id -u)/com.bhajanlal.proxy
$ sleep 3 && curl -s http://127.0.0.1:8788/health
```

---

## 3. Streaming + reasoning check

**Thinking:** A green `/health` only proves the process is up. The product
promise is *visible thinking*, so push one streamed request through the proxy
and confirm `reasoning_content` chunks arrive before the answer text.

```bash
$ curl -sN -H 'Authorization: Bearer bhajanlal-local' -H 'Content-Type: application/json' \
    http://127.0.0.1:8790/v1/chat/completions \
    -d '{"model":"bhajanlal/pro-max-2.5-free","messages":[{"role":"user","content":"Why is the sky blue? Think first, one line."}],"stream":true}' \
    | head -20
```

Expected: lines containing `"reasoning_content"` streaming first, then the
final `"content"` delta.

---

## 4. Phase orchestrator

**Thinking:** `--status` is read-only (safe anytime); running with no flags
executes the next phase cycle against `state.json`. The library phase runs
`build.py` for you.

```bash
$ python3 orchestrator.py --status     # inspect phase state, no side effects
$ python3 orchestrator.py              # advance the next phase
```

Phases in order: `library → foundation → evals → data → train → serve → selflearn`.

---

## 5. Skills library (931 skills / 81 pillars / coverage 900/900)

**Thinking:** Sources live in `skill_build/p1.py … p17.py`; `build.py` wipes
and regenerates `skills/` from them, so never hand-edit the output dir.
`auto_build.py` (launchd, every 15s) watches the sources and rebuilds on edit.
The endpoint rescans on mtime — no restart needed to see new skills.

```bash
$ cd ~/.config/opencode/skill_build && python3 build.py
# → OK: 931 skills, 81 pillars, coverage 900/900

$ curl -s http://127.0.0.1:8788/v1/skills | python3 -m json.tool | head -20
```

Pillars 55–59 hold the 100 media/visual/UI-UX modules (p14.py). Pillars 60–64
hold the 22 genuinely new List 9 skills (p17.py); the other 78 of the 100
OpenCode qualities map onto existing skills through `EXTRA_COVERS`. Coverage
tags L1–L9 are fully claimed — new skills ship with empty `covers`.

---

## 6. Evals

**Thinking:** Self-check first (validates the golden set without spending
inference), then the real score against the 0.75 pass@1 target.

```bash
$ python3 evals/harness.py --self-check   # validate golden cases
$ python3 evals/harness.py --list         # show cases
$ python3 evals/harness.py --run --local  # score local model, pass@1 vs 0.75
```

**List 9 suite** (100 cases, one per essential LLM quality — diagnostic only,
never mixed into golden). `--min-pass1 0` measures an honest baseline without
failing; results go to a suite-named file so the golden baseline is safe:

```bash
$ python3 evals/harness.py --self-check --cases evals/list9/cases.jsonl
$ python3 evals/harness.py --run --cases evals/list9/cases.jsonl --min-pass1 0
```

Regenerate the suite after editing specs: `python3 evals/list9/gen_list9.py`
(details in `evals/list9/README.md`).

---

## 7. One-shot inference

**Thinking:** Fastest way to sanity-check the model without touching the server.

```bash
$ python3 train/infer.py "Write a Python function to reverse a string."
```

---

## 8. Public tunnel (managed, one only)

**Thinking:** Exactly ONE cloudflared should exist — the launchd-managed one
(`KeepAlive`, publishes the :8080 auth proxy). Manual duplicates steal the
"which URL is live" question; kill them only after confirming the PID really
is cloudflared (PID reuse safety).

```bash
$ pgrep -fl cloudflared          # expect a single com.ashlee.bhajanlal-tunnel child
$ ps -p <PID> -o pid,command     # verify BEFORE killing
$ kill <PID>

# current published URL (quick-tunnel → changes on every restart):
$ grep -aoE 'https://[a-z0-9-]+\.trycloudflare\.com' \
    ~/.config/opencode/skill_build/state/logs/tunnel.log | tail -1

# bounce the managed tunnel:
$ launchctl kickstart -k gui/$(id -u)/com.ashlee.bhajanlal-tunnel
```

Stable-URL fix = the VPS route (§10), not more tunnels.

---

## 9. Feedback loop (self-learning)

**Thinking:** Feedback lands in `selflearn/harvest/feedback.jsonl`; the weekly
cycle (harvest → verify → train → eval → promote) consumes it once armed.

```bash
$ curl -s -X POST http://127.0.0.1:8788/v1/feedback -H 'Content-Type: application/json' \
    -d '{"session_id":"s1","signal":"thumbs_up","release":"bhajanlal-pro-max-2","timestamp":"2026-11-23T10:00:00","consent":true}'
$ curl -s http://127.0.0.1:8788/v1/feedback     # harvest count
```

---

## 10. GitHub release (gh lives in ~/.local/bin — no Homebrew on this Mac)

**Thinking:** Device flow keeps the token out of chat; commit identity is
repo-local, and anything >100MB is already excluded by `.gitignore`
(checkpoints, node_modules, the 348MB archive).

```bash
$ ~/.local/bin/gh auth login --hostname github.com --git-protocol https --web
$ ~/.local/bin/gh auth status

$ git add -A && git commit -m "feat: portable public release"
$ gh repo create Bhajanlal-App --public --source=. --push
$ gh release create v1.0 --title "v1.0" --notes "Portable public release"
```

---

## 11. VPS deploy (fixed URL — the one-liner that never breaks)

**Thinking:** One-time Oracle signup (their step, needs card/CAPTCHA), then a
single script rsyncs endpoint + ~950MB model, installs CPU torch in a venv,
sets up systemd + swap, and opens the firewall. Expect several minutes.

```bash
$ ssh -o ConnectTimeout=10 -o BatchMode=yes ubuntu@YOUR_VPS_IP 'echo connected'

$ ./deploy/deploy-to-vps.sh ubuntu@YOUR_VPS_IP     # run from repo root

$ curl -s http://YOUR_VPS_IP:8788/health           # → {"status":"ok",...}
```

Then point every client at the fixed address (never changes again):

```bash
$ curl -s http://YOUR_VPS_IP:8788/opencode.json -o ~/.config/opencode/opencode.json
# baseURL: "http://YOUR_VPS_IP:8788/v1"
```

Guide: `deploy/FREE-VPS-GUIDE.md` · key already generated: `~/.ssh/id_ed25519`.
