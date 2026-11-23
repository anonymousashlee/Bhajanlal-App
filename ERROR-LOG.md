# Bhajanlal-App Error Log

Consolidated inventory of errors found across the app, self-learning loop, and
supporting services. Each entry: source, symptom, root cause, fix status.

## 1. `backend error: Separator is not found, and chunk exceed the limit`
- **Source:** backend.py (both copies) `except Exception` handlers at L2212/L2322 (chat_error / stream_error).
- **Symptom:** opencode client shows "Retry due · attempt 3 · backend error: Separator is not found, and chunk exceed the limit"; ~30% of self-learning LLM cycles fail with `no JSON in reply (exit 1)`.
- **Root cause:** `opencode_stream()` iterated `proc.stdout` with `async for raw in proc.stdout`, which uses asyncio's `StreamReader` with the default 64 KB line limit. A single SSE/JSON event line longer than 64 KB raised `asyncio.LimitOverrunError` (streams.py:619). Also surfaced through `opencode run` subprocess output.
- **Fix:** added `limit=4 * 1024 * 1024` to all three `asyncio.create_subprocess_exec` calls (opencode_complete, opencode_stream, _opencode_models). ✅

## 2. LLM analysis failures (~23/56 cycles, "no JSON in reply" / "bad JSON")
- **Source:** `~/.config/opencode/skill_build/selflearn.py` `llm_analyze()`.
- **Symptom:** `llm=failed` in cycle reports; raw output saved for debugging.
- **Root causes:**
  - `opencode run` exited non-zero (free-limit 429 / upstream errors) with no retry.
  - `stderr` was discarded, so failure reasons were opaque.
  - JSON depth-scanner escape handling was broken: `ch == "\\\\"` (two backslashes in string) never matched a single backslash, desyncing string parsing on any `\"` escape.
- **Fix:** retry up to 3 times with backoff; capture stderr into the failure reason; fix escape comparison to `ch == "\\"`. ✅

## 3. Free-limit (429) provider failures (472 in error-report)
- **Source:** endpoint.py `upstream_chain()` / `stream_completion()`.
- **Symptom:** `provider.free-limit` idle failures; all candidates exhausted.
- **Root cause:** upstream account-wide rate limits; endpoint already falls back across the model chain and surfaces `Retry-After`.
- **Fix:** existing fallback chain retained; no change beyond ensuring the LimitOverrunError fix (#1) stops aborting runs early. ⚠️ partially mitigated (upstream account limits).

## 4. `compaction.failed` (1 occurrence)
- **Source:** OpenCode internal.
- **Root cause:** compaction summary template mismatch; not in our code.
- **Fix:** none (upstream). ⚠️ upstream.

## 5. Endpoint 502s / EMFILE (error-report §2)
- **Source:** endpoint.py `do_POST` / `_stream_chat`.
- **Symptom:** repeated 502 on `/v1/chat/completions`.
- **Root cause:** upstream failures (see #1, #3) + fd pressure; endpoint already calls `_raise_fd_limit()`.
- **Fix:** #1 reduces aborts; fd limit retained. ⚠️ partially mitigated.

## 6. Tunnel "Unauthorized: Tunnel not found"
- **Source:** cloudflared tunnel log.
- **Symptom:** retries with "Tunnel not found" (stale tunnel URL / expired tunnel).
- **Root cause:** ephemeral trycloudflare tunnel registration; launchd `com.ashlee.bhajanlal-tunnel` re-registers.
- **Fix:** ensure only the launchd tunnel unit runs (duplicate tunnels killed). ⚠️ monitor.

## 7. Branding leak: outbound `model` field could be raw `opencode/*`
- **Source:** backend.py + both endpoint.py copies (emission sites).
- **Symptom:** responses/headers/catalog could expose `opencode/mimo-v2.6-flash-free`.
- **Fix:** added `public_model()` helper; patched all emission sites (`_format_chat`, stream base/delta, X-Bhajanlal-Model header, agent finish/emit, catalog upstream); stripped raw `opencode/*` ids from `/v1/models` catalogs. Routing/aliases untouched. ✅

## 8. Security: drive-by RCE via legacy endpoint ACAO: *
- **Source:** legacy endpoint.py (`ACAO: *` at 5 sites, keyless POST).
- **Symptom:** any webpage could reach `opencode run --auto` (RCE).
- **Fix:** origin-restricted CORS (loopback only) + Origin/Host validation in do_GET/do_POST. ✅

## 9. Security: backend auth no-op (`_auth_ok` always True)
- **Source:** backend.py `_auth_ok`.
- **Fix:** real key check against `s.api_key`/`extra_keys` with `hmac.compare_digest`, localhost bypass when `allow_localhost`. ✅

## 10. Security: backend CORS default `*`
- **Source:** backend.py `_cors_headers` + env default.
- **Fix:** filter `"*"`; echo origin only for loopback/configured origins; env default `""`. ✅

## 11. Security: proxy string compare (`==`) + unauthenticated OPTIONS
- **Source:** model-ops/proxy.py `_authorized`, `do_OPTIONS`.
- **Fix:** `hmac.compare_digest`; OPTIONS requires auth. ✅

## 12. Approval backlog (65 items pending, 0 approved)
- **Source:** self-learning candidates/proposals queues.
- **Status:** human-gated by design (safety gates). No auto-approval performed. Mechanism exists (`state/candidates/approved/`). Requires human action. ⚠️ human action required.

## 13. LLM analysis ~30% failure rate
- **Source:** self-learning loop.
- **Status:** addressed by #1 and #2. ⚠️ monitor next cycles.

---
Generated during the "fix all errors" pass.
