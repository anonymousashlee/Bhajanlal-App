# List 9 eval suite (100 essential LLM qualities)

100 objectively-checkable cases, one per quality from the user's List 9
(5 pillars: 60 language/code craft, 61 agentic tool use, 62 speed/token
efficiency, 63 context/debugging, 64 honesty/workflow discipline).

Coverage tags: `L9-1` … `L9-100` — mapped in the skill library
(`skill_build/p17.py`): 22 genuinely new skills, 78 mapped onto existing
skills via `EXTRA_COVERS` (the library's p8/p9 convention).

## Layout

- `gen_list9.py` — the source of truth. All 100 specs live there; it
  validates every record against the real harness validator before
  writing, and asserts ids are exactly `l9-001`…`l9-100`.
- `cases.jsonl` — generated suite. **Do not hand-edit**; regenerate:

      python3 evals/list9/gen_list9.py

## Running

    # schema validation (exit 0)
    python3 evals/harness.py --self-check --cases evals/list9/cases.jsonl

    # live baseline (never fails on low score)
    python3 evals/harness.py --run --cases evals/list9/cases.jsonl --min-pass1 0

Results go to `evals/results/local_list9_last_run.json` (or
`list9_last_run.json` when run against the endpoint) — suite-named, so
the golden baseline (`local_last_run.json` / `last_run.json`) is never
overwritten.

## Why a separate suite

The golden suite (`evals/golden/cases.jsonl`, 28 cases, honest baseline
10/28 = 0.357, target 0.75) measures the release blocker. Mixing these
100 cases into it would make the baseline meaningless. This suite is a
**diagnostic**: it measures where the model actually stands on the 100
qualities before training data targets them.

Check mix: constraint=59, tests=14, exact-match=13, jsonschema=13,
abstain=1. Every case is machine-scored (no LLM judge).

## Status / next steps

- Built and validated; scoring discrimination tested (ideal answers
  pass, wrong answers fail on 17+ probes).
- Not wired into any train script — that's deliberate: the honest
  baseline should be measured first, then training data can target the
  failing pillars.
- Suggested next step: run the baseline above while the endpoint is
  idle, group failures by pillar (`family`/id prefix), and only then
  decide what training data to add.

## Known scoring quirks (harness-side, shared with golden)

- `extract_code` falls back to the longest code-looking run when there
  is no fence; `import`/`from` lines count as code (fixed — otherwise a
  bare `from unittest.mock import patch` line was mistaken for prose).
- `tests` checks run model code + assertion preamble in one subprocess
  (15s timeout), so prompts that need `unittest`/`asyncio`/`sqlite3`
  must ask the model to import them — the class body executes before
  the appended assertions.
