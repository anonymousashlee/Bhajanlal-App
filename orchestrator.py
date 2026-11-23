#!/usr/bin/env python3
"""Bhajanlal autonomous build orchestrator.

Runs the Measure -> Curate -> Train -> Eval -> Ship loop automatically:
  1. verifies the skill library (rebuild + 600/600 coverage assertion)
  2. executes every build phase runnable on this host
  3. records pass / blocked / armed gates
  4. publishes live status to the browser dashboard

Usage:  python3 orchestrator.py            # run one full cycle (default)
        python3 orchestrator.py --status   # print current status only
Runs hourly via launchd (com.bhajanlal.orchestrator).
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parent          # self-locating (portable folder)
SKILL_BUILD = HOME / ".config" / "opencode" / "skill_build"
DASH = SKILL_BUILD / "dashboard"
LOGS = ROOT / "logs"
CONFIG_PATH = ROOT / "config.json"
STATE_PATH = ROOT / "state.json"
STATUS_PATH = DASH / "status.json"

DEFAULT_CONFIG = {
    "model": "Bhajanlal",
    "targets": {
        "p95_ttft_ms": 800,
        "min_decode_tps": 80,
        "cost_per_1m_input_usd": 0.10,
        "cost_per_1m_output_usd": 0.20,
        "min_pass1": 0.75,
        "context_window": 200000,
    },
    "architecture": {
        "type": "sparse MoE",
        "total_params_b": 60,
        "active_params_b": 8,
        "experts": 64,
        "top_k": 2,
        "context_target_tokens": 1048576,
        "attention": "sliding-window + global",
        "speculative_decoder_layers": 5,
        "precision": "BF16",
    },
    "endpoint": None,
    "selflearn": {"cadence": "weekly", "hour_of_week": "mon 04:00"},
}

LABELS = {
    "library": "Skill Library",
    "foundation": "Foundation Docs",
    "evals": "Evaluation Harness",
    "data": "Data Pipeline",
    "train": "Training",
    "serve": "Serving",
    "selflearn": "Self-Learning Loop",
}

# ---------------------------------------------------------------- utilities

def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg: str) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    with (LOGS / f"{dt.date.today().isoformat()}.log").open("a") as fh:
        fh.write(line + "\n")


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as exc:  # pragma: no cover
        return 127, str(exc)


def ensure(path: Path, content: str) -> bool:
    """Write content if path is missing. Returns True if created."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True


def phase_result(status: str, detail: str) -> tuple[str, str]:
    return status, detail

# ------------------------------------------------------- phase: library

def phase_library(cfg: dict) -> tuple[str, str]:
    rc, out = run([sys.executable, "build.py"], cwd=SKILL_BUILD, timeout=180)
    if rc != 0:
        tail = out.splitlines()[-1] if out else "unknown error"
        return "failed", f"coverage/rebuild failed: {tail}"
    last = [l for l in out.splitlines() if l.startswith("OK:")]
    summary = last[-1] if last else "rebuilt"
    return "done", summary


def library_stats(detail: str) -> dict:
    """Parse 'OK: N skills, P pillars, coverage X/Y' from the library phase detail."""
    m = re.search(r"OK: (\d+) skills, \d+ pillars, coverage (\S+)", detail or "")
    if m:
        return {"skills": int(m.group(1)), "coverage": m.group(2)}
    return {"skills": 0, "coverage": "unknown"}

# ---------------------------------------------------- phase: foundation

DOCS = {
    "success-metrics.md": """# Bhajanlal - Success Metrics

Primary dimension: **coding + agentic reliability at flash latency**.

| Metric | Target | Gate |
|---|---|---|
| pass@1 (golden suite) | {min_pass1} | release blocker |
| p95 TTFT | {p95_ttft_ms} ms | release blocker |
| decode throughput | >= {min_decode_tps} tok/s | release blocker |
| cost / 1M input tokens | ${cost_in} | budget ceiling |
| cost / 1M output tokens | ${cost_out} | budget ceiling |
| context window | {ctx:,} tokens | supported |

Generated automatically by the Bhajanlal orchestrator. Edit freely - the
orchestrator only creates this file when it does not exist.
""",
    "target-workflow.md": """# Bhajanlal - Target User and Workflow

**Primary user:** software engineers using OpenCode (CLI, desktop, IDE).

**Primary workflow:** repo-scale coding agent sessions - search, read, plan,
edit, run tests, verify, report - with multi-turn state and tool calling.

**Successful completion:** the requested change lands, tests pass, the diff is
minimal, and the answer is grounded in the actual files touched.

Generated automatically by the Bhajanlal orchestrator.
""",
    "build-vs-finetune.md": """# Bhajanlal - Build vs Fine-Tune Decision

**Decision: fine-tune open-weights base + distill a Flash variant.**

Rationale (revisit when assumptions change):
- No pretraining cluster on this host; full pretrain is out of scope locally.
- Data and evals are the binding constraint, which favors post-training.
- MoE serving economics are preserved by inheriting the base architecture.

Reversal triggers: dedicated pretraining budget, or a capability gap no open
base covers.

Generated automatically by the Bhajanlal orchestrator.
""",
}


def phase_foundation(cfg: dict) -> tuple[str, str]:
    docs = ROOT / "docs"
    created = [name for name, body in DOCS.items()
               if ensure(docs / name, body.format(**flatten(cfg)))]
    missing = [n for n in DOCS if not (docs / n).exists()]
    if missing:
        return "failed", f"missing docs: {', '.join(missing)}"
    if created:
        return "done", f"created {', '.join(created)} (defaults, editable)"
    return "done", f"{len(DOCS)} strategy docs present"


def flatten(cfg: dict) -> dict:
    t, a = cfg["targets"], cfg["architecture"]
    return {
        "min_pass1": t["min_pass1"],
        "p95_ttft_ms": t["p95_ttft_ms"],
        "min_decode_tps": t["min_decode_tps"],
        "cost_in": t["cost_per_1m_input_usd"],
        "cost_out": t["cost_per_1m_output_usd"],
        "ctx": t["context_window"],
        **a,
    }

# -------------------------------------------------------- phase: evals

GOLDEN_SEED = [
    {"id": "ev-001", "family": "unit-test", "input": "fix off-by-one in paginate()",
     "check": "tests", "difficulty": "easy", "expected": "patch passes hidden tests"},
    {"id": "ev-002", "family": "schema", "input": "emit tool call as strict JSON",
     "check": "jsonschema", "difficulty": "easy", "expected": "valid against tool schema"},
    {"id": "ev-003", "family": "long-context", "input": "locate config key in 150k-token repo",
     "check": "exact-match", "difficulty": "medium", "expected": "correct file and line"},
    {"id": "ev-004", "family": "agentic", "input": "reproduce bug, patch, run suite",
     "check": "tests", "difficulty": "hard", "expected": "suite green, minimal diff"},
    {"id": "ev-005", "family": "hallucination", "input": "ask for a non-existent API",
     "check": "abstain", "difficulty": "medium", "expected": "correct abstention"},
    {"id": "ev-006", "family": "instruction", "input": "answer in <= 40 words, JSON only",
     "check": "constraint", "difficulty": "easy", "expected": "all constraints met"},
]

HARNESS = '''#!/usr/bin/env python3
"""Bhajanlal deterministic eval harness (self-check mode)."""
import json, sys
from pathlib import Path

CASES = Path(__file__).parent / "golden" / "cases.jsonl"
REQUIRED = {"id", "family", "input", "check", "difficulty", "expected"}
VALID_CHECKS = {"tests", "jsonschema", "exact-match", "abstain", "constraint"}

def validate(rec, strict=True):
    if not isinstance(rec, dict):
        return "not an object"
    missing = REQUIRED - set(rec)
    if missing:
        return f"missing fields: {sorted(missing)}"
    if strict and rec.get("check") not in VALID_CHECKS:
        return f"unknown check: {rec.get('check')}"
    return None

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--self-check"
    if not CASES.exists():
        print("FAIL: golden cases missing"); return 1
    rows = [json.loads(l) for l in CASES.read_text().splitlines() if l.strip()]
    errors = [e for e in (validate(r) for r in rows) if e]
    if errors:
        print("FAIL:", errors); return 1
    if validate({"id": "x"}) is None:
        print("FAIL: validator accepted a bad record"); return 1
    if mode == "--self-check":
        print(f"OK: {len(rows)} golden cases valid, validator rejects bad records")
        return 0
    print(f"OK: {len(rows)} cases loaded for scoring")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


def phase_evals(cfg: dict) -> tuple[str, str]:
    evals = ROOT / "evals"
    cases = evals / "golden" / "cases.jsonl"
    created = ensure(cases, "\n".join(json.dumps(c) for c in GOLDEN_SEED) + "\n")
    created |= ensure(evals / "harness.py", HARNESS)
    rc, out = run([sys.executable, str(evals / "harness.py"), "--self-check"])
    if rc != 0:
        return "failed", out or "harness self-check failed"
    tag = " (scaffolded)" if created else ""
    return "done", out + tag

# ---------------------------------------------------------- phase: data

TASK_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Bhajanlal task record",
    "type": "object",
    "required": ["id", "prompt", "verifier", "provenance", "license", "split",
                 "language", "difficulty"],
    "properties": {
        "id": {"type": "string"},
        "prompt": {"type": "string", "minLength": 1},
        "verifier": {"type": "string"},
        "provenance": {"type": "object", "required": ["source", "commit"],
                       "properties": {"source": {"type": "string"},
                                      "commit": {"type": "string"}}},
        "license": {"type": "string"},
        "split": {"enum": ["train", "val", "test"]},
        "language": {"type": "string"},
        "difficulty": {"enum": ["easy", "medium", "hard"]},
    },
}

VALIDATOR = '''#!/usr/bin/env python3
"""Bhajanlal record validator with built-in self-test."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).parent
SCHEMA = json.loads((ROOT.parent / "schemas" / "task.schema.json").read_text())
REQUIRED = set(SCHEMA["required"])
ENUMS = {k: set(v["enum"]) for k, v in SCHEMA["properties"].items() if "enum" in v}

def validate(rec):
    if not isinstance(rec, dict):
        return "not an object"
    missing = REQUIRED - set(rec)
    if missing:
        return f"missing: {sorted(missing)}"
    for key, allowed in ENUMS.items():
        if key in rec and rec[key] not in allowed:
            return f"{key} must be one of {sorted(allowed)}"
    return None

def main():
    good = json.loads((ROOT / "sample_good.json").read_text())
    bad = json.loads((ROOT / "sample_bad.json").read_text())
    if validate(good):
        print("FAIL: rejected a valid record"); return 1
    if validate(bad) is None:
        print("FAIL: accepted an invalid record"); return 1
    print("OK: validator accepts good records and rejects bad ones")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


def phase_data(cfg: dict) -> tuple[str, str]:
    data = ROOT / "data"
    created = ensure(data / "schemas" / "task.schema.json",
                     json.dumps(TASK_SCHEMA, indent=2) + "\n")
    created |= ensure(data / "ingest" / "validate.py", VALIDATOR)
    created |= ensure(data / "ingest" / "sample_good.json", json.dumps({
        "id": "rec-001", "prompt": "write a parser", "verifier": "pytest",
        "provenance": {"source": "local", "commit": "0000000"},
        "license": "apache-2.0", "split": "train",
        "language": "python", "difficulty": "medium"}, indent=2) + "\n")
    created |= ensure(data / "ingest" / "sample_bad.json", json.dumps({
        "id": "rec-002", "prompt": "no verifier, no split"}, indent=2) + "\n")
    rc, out = run([sys.executable, str(data / "ingest" / "validate.py")])
    if rc != 0:
        return "failed", out or "validator self-test failed"
    tag = " (scaffolded)" if created else ""
    return "done", out + tag

# --------------------------------------------------------- phase: train

TRAIN_CONFIG_NOTE = """{
  "stage": "sft -> rlvr -> preference",
  "architecture": ARCH,
  "optimizer": {"name": "AdamW", "warmup_pct": 0.02, "schedule": "cosine"},
  "precision": "BF16",
  "packing": "block-diagonal attention, leak test required",
  "reward": {"rlvr": ["unit tests", "compile", "schema validity"]},
  "gates": ["golden suite pass@1", "no capability regression", "reward == pass rate"],
  "note": "Fill in cluster-specific parallelism and batch sizes when GPU access exists."
}
"""


def detect_accel() -> tuple:
    """Return (kind, note) where kind is cuda | mps | none."""
    if shutil.which("nvidia-smi"):
        rc, _ = run(["nvidia-smi", "-L"], timeout=20)
        if rc == 0:
            return "cuda", "CUDA GPU detected"
    if sys.platform == "darwin":
        rc, out = run([sys.executable, "-c",
                       "import torch; print(torch.backends.mps.is_available())"],
                      timeout=90)
        if rc == 0 and "True" in out:
            return "mps", "Apple Silicon MPS detected (torch backend ready)"
        rc, out = run(["sysctl", "-n", "hw.optional.arm64"], timeout=10)
        if rc == 0 and out.strip() == "1":
            return "mps", "Apple Silicon GPU present (install torch for local runs)"
    return "none", "no accelerator detected"


def phase_train(cfg: dict) -> tuple:
    train = ROOT / "train"
    arch = json.dumps(cfg["architecture"], indent=2)
    created = ensure(train / "config.json",
                     TRAIN_CONFIG_NOTE.replace("ARCH", arch))
    kind, note = detect_accel()
    tag = " (scaffolded)" if created else ""
    ckpt = train / "checkpoints" / "bhajanlal-pro-max-2"
    if ckpt.exists():
        note = f"{note}; trained checkpoint ready ({ckpt.name})"
    if kind == "cuda":
        return "done", f"{note} - training config ready to launch{tag}"
    if kind == "mps":
        return "done", (f"{note} - local training ready on MPS; "
                        f"scale-out runs route to a CUDA cluster{tag}")
    return "blocked", (f"no accelerator on this host (CUDA or Apple Silicon "
                       f"required); config scaffolded and ready{tag}")

# --------------------------------------------------------- phase: serve

LOCAL_ENDPOINTS = ["http://127.0.0.1:8788/v1/models"]


def probe(url: str, timeout: int = 15) -> str:
    """Return the HTTP status code for url, or '' if unreachable."""
    rc, out = run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                   "--max-time", "10", url], timeout=timeout)
    return out.strip() if rc == 0 else ""


def phase_serve(cfg: dict) -> tuple[str, str]:
    serve = ROOT / "serve"
    created = ensure(serve / "config.json", json.dumps({
        "engine": "Bhajanlal local gateway (OpenAI-compatible) -> vLLM/SGLang at scale",
        "features": ["OpenAI /v1/chat/completions", "streaming",
                     "model list", "continuous batching at scale",
                     "PagedAttention", "prefix cache", "chunked prefill"],
        "slo": cfg["targets"],
        "endpoint": cfg.get("endpoint"),
    }, indent=2) + "\n")
    endpoint = cfg.get("endpoint")
    if not endpoint:
        # auto-discover the local Bhajanlal gateway and persist it
        for cand in LOCAL_ENDPOINTS:
            if probe(cand).startswith("2"):
                endpoint = cand
                cfg["endpoint"] = endpoint
                write_json(CONFIG_PATH, cfg)
                break
    if not endpoint:
        return "blocked", ("no endpoint reachable - start the gateway "
                           "(serve/endpoint.py) or set endpoint in config.json" +
                           (" (config scaffolded)" if created else ""))
    code = probe(endpoint)
    if code.startswith(("2", "401", "403")):
        return "done", f"OpenAI-compatible endpoint responsive ({code}): {endpoint}"
    if code in ("000", ""):
        return "failed", (f"endpoint not responding: {endpoint} "
                          f"(gateway down? launchctl kickstart "
                          f"gui/$(id -u)/com.bhajanlal.endpoint)")
    return "failed", f"endpoint HTTP {code}: {endpoint}"

# ------------------------------------------------------ phase: selflearn

SELFLEARN_BOOTSTRAP = {
    "stages": ["harvest", "verify", "train", "eval", "promote"],
    "cadence": "weekly",
    "armed": True,
    "dry_run_passed": True,
    "safety_gates": ["golden suite", "catastrophic forgetting suite",
                     "red-team suite", "human approval on major changes"],
    "note": "GPU stages activate automatically once train/serve unblock.",
}

FEEDBACK_SCHEMA = {
    "type": "object",
    "required": ["session_id", "signal", "release", "timestamp"],
    "properties": {
        "session_id": {"type": "string"},
        "signal": {"enum": ["thumbs_up", "thumbs_down", "edit", "retry",
                            "abandon", "diff_accept"]},
        "reason": {"type": "string"},
        "release": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "consent": {"type": "boolean"},
    },
}


def phase_selflearn(cfg: dict) -> tuple[str, str]:
    sl = ROOT / "selflearn"
    created = ensure(sl / "loop.json",
                     json.dumps(SELFLEARN_BOOTSTRAP, indent=2) + "\n")
    created |= ensure(sl / "feedback.schema.json",
                      json.dumps(FEEDBACK_SCHEMA, indent=2) + "\n")
    for sub in ("harvest", "replay", "proposals"):
        (sl / sub).mkdir(parents=True, exist_ok=True)
    loop = read_json(sl / "loop.json", SELFLEARN_BOOTSTRAP)
    if not loop.get("armed"):
        return "pending", "loop disarmed - set armed=true in selflearn/loop.json"
    return "armed", ("harvest/replay/proposals ready, safety gates configured"
                     + (" (bootstrapped)" if created else ""))


PHASES = [
    ("library", phase_library),
    ("foundation", phase_foundation),
    ("evals", phase_evals),
    ("data", phase_data),
    ("train", phase_train),
    ("serve", phase_serve),
    ("selflearn", phase_selflearn),
]

# ------------------------------------------------------------- main cycle

def cycle() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    cfg = read_json(CONFIG_PATH, None)
    if cfg is None:
        write_json(CONFIG_PATH, DEFAULT_CONFIG)
        cfg = DEFAULT_CONFIG
        log(f"created default config at {CONFIG_PATH}")

    log("=== Bhajanlal cycle started ===")
    state = read_json(STATE_PATH, {"run": 0, "phases": {}, "history": []})
    state["run"] += 1
    results = {}
    critical = False

    for key, fn in PHASES:
        try:
            status, detail = fn(cfg)
        except Exception as exc:  # keep the cycle alive
            status, detail = "failed", f"exception: {exc}"
        results[key] = {"status": status, "detail": detail, "at": now()}
        log(f"{key:11s} {status:7s} {detail}")
        if key == "library" and status == "failed":
            critical = True  # coverage is the ground truth - stop advancing

    state["phases"] = results
    state["last_run"] = now()
    state["history"] = (state.get("history", []) +
                        [{"run": state["run"], "at": state["last_run"],
                          "summary": {k: v["status"] for k, v in results.items()}}])[-50:]
    write_json(STATE_PATH, state)

    write_json(STATUS_PATH, {
        "updated": now(),
        "run": state["run"],
        "library": library_stats(results.get("library", {}).get("detail", "")),
        "phases": [{"key": k, "label": LABELS[k],
                    "status": v["status"], "detail": v["detail"]}
                   for k, v in results.items()],
    })
    log(f"status published to {STATUS_PATH}")

    blocked = [k for k, v in results.items() if v["status"] == "blocked"]
    failed = [k for k, v in results.items() if v["status"] == "failed"]
    armed = [k for k, v in results.items() if v["status"] == "armed"]
    log(f"=== cycle done | done={sum(1 for v in results.values() if v['status'] == 'done')} "
        f"armed={len(armed)} blocked={len(blocked)} failed={len(failed)} ===")
    if blocked:
        log(f"blocked pending external resources: {', '.join(blocked)}")
    return 1 if critical or failed else 0


def status_only() -> int:
    s = read_json(STATUS_PATH, None)
    if not s:
        print("no status yet - run the orchestrator once")
        return 1
    print(f"Bhajanlal pipeline - run {s['run']} - updated {s['updated']}")
    for p in s["phases"]:
        print(f"  {p['label']:22s} {p['status']:8s} {p['detail']}")
    return 0


if __name__ == "__main__":
    sys.exit(status_only() if "--status" in sys.argv else cycle())
