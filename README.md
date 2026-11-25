
## Troubleshooting

- **Endpoint returns 503 / "backend busy"**: The semaphore cap (MAX_CONCURRENT) is exhausted. Wait a few seconds or raise `BHAJANLAL_MAX_CONCURRENT`. Check `/health` for `active_requests`.
- **Local model fails to load**: Ensure `LOCAL_CKPT` points at a valid checkpoint and torch is installed. Inspect the printed `_LOCAL["error"]` in endpoint logs. Set `BHAIJANLAL_NO_CACHE=1` to bypass the golden cache while debugging.
- **Eval pass@1 lower than expected**: Run with `--bypass-cache` so results reflect the model, not cached product responses: `python3 evals/harness.py --run --bypass-cache`.
- **Orchestrator appears stuck**: Run `python3 orchestrator.py --status` to see phase states, or `python3 orchestrator.py --dry-run` to preview the next cycle without mutating state.
- **FD exhaustion (Errno 24)**: The backend raises the soft FD limit to the hard limit at startup; if still hit, raise the OS limit (`ulimit -n`) before launching.
- **Cache staleness**: Lower `BHAJANLAL_CACHE_TTL` or send `"cache": false` in the request body.

## Security notes

- The gateway is **open by default** (`_auth_ok` returns True) for local/free use. Set `BHAJANLAL_API_KEY` and disable `BHAJANLAL_ALLOW_LOCALHOST` to require a bearer token.
- The agent `shell` tool runs commands with `shell=True` inside the sandbox root (`BHAJANLAL_SANDBOX`). Disable it in public deployments via `BHAJANLAL_AGENT_SHELL=0`.
- CORS allows only explicitly configured origins plus localhost; wildcard `*` is rejected.
- No secrets are stored in the repo; configure providers via `BHAJANLAL_*` / `MIMO_API_KEY` / `MINIMAX_API_KEY` environment variables.
