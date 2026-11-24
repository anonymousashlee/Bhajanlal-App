#!/usr/bin/env python3
"""Catastrophic-forgetting check for Bhajanlal model promotion.

Compares a candidate eval result against a baseline (the last promoted model's
result) and fails if any previously-passing case regressed, or if aggregate
pass@1 dropped beyond a tolerance.

Usage:
  python3 evals/forgetting_check.py --baseline evals/results/baseline.json \
                                    --candidate evals/results/local_last_run.json
  python3 evals/forgetting_check.py --self-check   # smoke the comparison logic

Exit codes:
  0  no regression beyond tolerance
  1  regression detected or inputs invalid
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_TOLERANCE = 0.0  # no case-level regression allowed by default
MAX_PASS1_DROP = 0.05     # aggregate pass@1 may drop at most 5 points


def load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"FAIL: result file missing: {path}")
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        raise SystemExit(f"FAIL: invalid JSON in {path}: {exc}")


def compare(baseline: dict, candidate: dict, tolerance: float, max_drop: float) -> tuple[bool, list[str]]:
    b_results = {r["id"]: r for r in baseline.get("results", [])}
    c_results = {r["id"]: r for r in candidate.get("results", [])}

    msgs: list[str] = []
    regressed: list[str] = []
    new_cases: list[str] = []
    for cid, br in b_results.items():
        cr = c_results.get(cid)
        if cr is None:
            msgs.append(f"  MISSING in candidate: {cid}")
            continue
        if br.get("pass") and not cr.get("pass"):
            regressed.append(cid)
            msgs.append(f"  REGRESSED: {cid}  ({br.get('detail','')} -> {cr.get('detail','')})")

    for cid in c_results:
        if cid not in b_results:
            new_cases.append(cid)

    b_pass1 = baseline.get("pass1", 0.0)
    c_pass1 = candidate.get("pass1", 0.0)
    drop = b_pass1 - c_pass1
    if drop > max_drop:
        msgs.append(f"  AGGREGATE DROP: pass@1 {b_pass1:.3f} -> {c_pass1:.3f} "
                    f"(drop {drop:.3f} > {max_drop:.3f})")

    ok = (not regressed) and (drop <= max_drop)
    summary = [
        f"baseline pass@1 = {b_pass1:.3f} ({baseline.get('passed','?')}/{baseline.get('total','?')})",
        f"candidate pass@1 = {c_pass1:.3f} ({candidate.get('passed','?')}/{candidate.get('total','?')})",
        f"regressed cases: {len(regressed)}  new cases: {len(new_cases)}",
    ]
    return ok, summary + msgs


def self_check() -> int:
    # Synthetic comparison to exercise the logic.
    base = {
        "pass1": 0.8, "passed": 4, "total": 5,
        "results": [
            {"id": "a", "pass": True, "detail": "ok"},
            {"id": "b", "pass": True, "detail": "ok"},
            {"id": "c", "pass": False, "detail": "fail"},
        ],
    }
    cand_ok = {
        "pass1": 0.8, "passed": 4, "total": 5,
        "results": [
            {"id": "a", "pass": True, "detail": "ok"},
            {"id": "b", "pass": True, "detail": "ok"},
            {"id": "c", "pass": True, "detail": "ok"},  # improvement, not regression
        ],
    }
    cand_bad = {
        "pass1": 0.4, "passed": 2, "total": 5,
        "results": [
            {"id": "a", "pass": False, "detail": "now fails"},  # regression
            {"id": "b", "pass": True, "detail": "ok"},
            {"id": "c", "pass": True, "detail": "ok"},
        ],
    }
    ok1, _ = compare(base, cand_ok, 0.0, 0.05)
    ok2, _ = compare(base, cand_bad, 0.0, 0.05)
    if not (ok1 and not ok2):
        print("FAIL: self-check logic wrong")
        return 1
    print("OK: forgetting check self-test passes")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Bhajanlal catastrophic-forgetting check")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--baseline", type=Path)
    ap.add_argument("--candidate", type=Path)
    ap.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    ap.add_argument("--max-drop", type=float, default=MAX_PASS1_DROP)
    args = ap.parse_args()

    if args.self_check:
        return self_check()

    if not args.baseline or not args.candidate:
        print("FAIL: --baseline and --candidate required (or --self-check)")
        return 1
    baseline = load(args.baseline)
    candidate = load(args.candidate)
    ok, msgs = compare(baseline, candidate, args.tolerance, args.max_drop)
    print("\n".join(msgs))
    if ok:
        print("OK: no catastrophic forgetting detected")
        return 0
    print("FAIL: catastrophic forgetting / regression detected")
    return 1


if __name__ == "__main__":
    sys.exit(main())
