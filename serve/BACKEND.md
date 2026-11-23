# Bhajanlal Backend (model gateway + agentic runtime)

OpenAI-compatible backend on 127.0.0.1:8790 (override with BHAJANLAL_BACKEND_PORT).

## Start
  ./start-backend.sh
  # or
  BHAIJANLAL_BACKEND_PORT=8790 python3 backend.py

## Endpoints
  GET  /                          web chat UI (playground, same file as /ui)
  GET  /health
  GET  /metrics
  GET  /v1/models
  GET  /v1/skills                 Bhajanlal skill library (?q=<text> search, ?id=<skill> full workflow)
  POST /v1/chat/completions   (stream + non-stream, multimodal content, tools)
  POST /v1/agent/run           (multi-step tool loop)

## Skill library (every skill active)
  Source: ~/.config/opencode/skills/*/SKILL.md (live count from disk — 489 at
          time of writing, 35 pillars; new skills are picked up automatically
          via the mtime cache, no restart needed)
  Loader: skills.py  (mtime-cached scan; relevance scoring is microseconds)
  Every request gets a system block with:
    - the skills relevant to the message, inlined in full (Workflow + Output)
    - the complete index of every skill, so nothing is hidden from the model
    - instructions to load any other skill on demand via the `skill` tool
  Tools: `skill` {action: load|search|list|count, id?, query?, limit?}
  Agent responses carry "skills": {"applied": [...], "loaded": [...], "library": {...}}
  Mode: BHAJANLAL_SKILLS=full (default) | applied | off
  Same wiring exists in endpoint.py (port 8788), except the 0.5B local
  checkpoint, which gets a plain prompt (it can't digest the library).

## Models / providers
  bhajanlal, bhajanlal/flash, bhajanlal/beam, bhajanlal/nemotron  -> opencode free (mimo-v2.6-flash, beam, nemotron)
  bhajanlal/mimo, bhajanlal/mimo-flash  -> Xiaomi MiMo (BHAIJANLAL_MIMO_API_KEY)
  bhajanlal/minimax, bhajanlal/minimax-m3  -> MiniMax M3 (BHAIJANLAL_MINIMAX_API_KEY)
  bhajanlal/minimax-h3  -> MiniMax H3
  bhajanlal/paid  -> generic OpenAI-compatible (BHAIJANLAL_PAID_*)

If a paid key is missing, the backend transparently falls back to the free
opencode mimo-v2.6-flash-free upstream.

## Enable Xiaomi MiMo / MiniMax
  export BHAIJANLAL_MIMO_BASE_URL="https://api.xiaomimimo.com/v1"
  export BHAIJANLAL_MIMO_API_KEY="..."
  export BHAIJANLAL_MIMO_MODEL="mimo-v2.6-flash"
  export BHAIJANLAL_MINIMAX_BASE_URL="https://api.minimax.chat/v1"
  export BHAIJANLAL_MINIMAX_API_KEY="..."
  export BHAIJANLAL_MINIMAX_MODEL_M3="MiniMax-M2.7"
  export BHAIJANLAL_MINIMAX_MODEL_H3="MiniMax-H3"

## Agentic tools (built-in)
  skill (Bhajanlal skill library: load/search/list/count), calculator, get_time,
  read_file (sandboxed), list_dir (sandboxed), shell, edit_file (opt-in)
  Pass your own OpenAI function-calling tools via "tools" in /v1/agent/run.

## Omni / Ensemble ("greatest AI": compile all models together)
  Models: bhajanlal/bhajanlal (flagship, full ensemble), bhajanlal/pro-max (alias)
          bhajanlal/omni (default), bhajanlal/greatest, bhajanlal/ultimate,
          bhajanlal/ensemble, bhajanlal/best
  Aliases for Pro Max: bhajanlal/pro-max, bhajanlal/promax, "bhajanlal pro max"
  (case-insensitive). It uses the full OMNI spec: MiMo V2.6 Pro + Flash,
  MiniMax M3 + M3.1-Flash, any paid OpenAI-compatible endpoint, plus the free
  OpenCode fallback chain - i.e. every chat model compiled into one.
  Strategy: fans out the prompt to EVERY configured provider in parallel
  (MiMo V2.6 Flash/Pro + MiniMax M3 + free opencode chain), then uses the
  strongest available model as a judge to score each candidate (accuracy,
  helpfulness, completeness, clarity) and return the winner. For the omni
  aliases the judge also synthesizes a single "compiled" answer that merges
  the strongest parts of all candidates (response marks compiled: true).
  Response includes x_bhajanlal.ensemble with candidates, scores, judge,
  winner_index, reason, compiled. Falls back to consensus (most-agreed
  answer) if the judge fails. Fan-out size capped by
  BHAIJANLAL_ENSEMBLE_MAX (default 5) to keep latency sane.
  Streaming works too: live stage events (fanout / judge / compiled) arrive
  while the fan-out runs, then the compiled answer is replayed as SSE chunks.
  Agent mode (/v1/agent/run) with an omni model runs a fast tool loop and then
  compiles the final answer across all models (set "compile_steps": true to
  fan out on every step instead).
  A single-provider setup (free opencode only) is capped by
  BHAJANLAL_ENSEMBLE_MAX_SINGLE (default 3).
  Requires provider keys for real diversity; on free tier only, all
  candidates share the opencode free chain.

## Multimodal
  messages[].content may be a list of {type:"text"} / {type:"image_url"} parts.
  Paid providers forward images verbatim; the free opencode provider degrades to text.

## OpenCode client config
  baseURL: http://127.0.0.1:8790/v1
  apiKey: bhajanlal-local (or BHAIJANLAL_API_KEY)
