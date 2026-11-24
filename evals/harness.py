#!/usr/bin/env python3
"""Bhajanlal eval harness.

Modes (default is --self-check):
  --self-check   Validate the golden case file (schema only).
  --run          Send every case to the endpoint and score pass@1.
  --verbose      With --run, print per-case detail.
  --list         Print case ids and checks.

Options:
  --cases PATH   Use an alternate case file (e.g. evals/list9/cases.jsonl)
                 instead of golden/cases.jsonl. Non-golden runs write their
                 results to a suite-named file so they never clobber the
                 golden baseline (last_run.json / local_last_run.json).
  --min-pass1 F  Override the config.json min_pass1 target for this run
                 (use 0 to measure a fresh baseline without failing).

Exit codes:
  0  self-check OK, or run finished at/above the min_pass1 target
  1  validation failure, endpoint unreachable, or run below target
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
CASES = HERE / "golden" / "cases.jsonl"
CONFIG = HERE.parent / "config.json"
RESULTS_DIR = HERE / "results"

DEFAULT_ENDPOINT = os.environ.get(
    "BHAIJANLAL_ENDPOINT", "http://127.0.0.1:8788/v1/chat/completions"
)
DEFAULT_MODEL = os.environ.get("BHAIJANLAL_MODEL", "bhajanlal/bhajanlal")

REQUIRED = {"id", "family", "check", "difficulty", "prompt"}
VALID_CHECKS = {"tests", "jsonschema", "exact-match", "abstain", "constraint"}
CHECK_REQUIRED = {
    "tests": {"assertions"},
    "jsonschema": {"schema"},
    "exact-match": {"expected"},
    "abstain": {"abstain_patterns"},
    "constraint": {"constraints"},
}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_CONSTRAINTS = {"max_words", "min_words", "json_only", "json_array_len",
                     "json_array_sum", "json_object_keys", "bullet_count",
                     "no_code_blocks", "forbidden", "required"}

FENCE_RE = re.compile(r"```[a-zA-Z0-9_+-]*\n(.*?)```", re.DOTALL)


# --------------------------------------------------------------------------
# case validation
# --------------------------------------------------------------------------

def validate(rec) -> str | None:
    if not isinstance(rec, dict):
        return "not an object"
    missing = REQUIRED - set(rec)
    if missing:
        return f"missing fields: {sorted(missing)}"
    check = rec.get("check")
    if check not in VALID_CHECKS:
        return f"unknown check: {check!r}"
    extra = CHECK_REQUIRED[check] - set(rec)
    if extra:
        return f"check {check!r} missing fields: {sorted(extra)}"
    if rec.get("difficulty") not in VALID_DIFFICULTIES:
        return f"bad difficulty: {rec.get('difficulty')!r}"
    if check == "tests" and not isinstance(rec["assertions"], list):
        return "assertions must be a list"
    if check == "exact-match":
        exp = rec["expected"]
        if isinstance(exp, str):
            pass
        elif not (isinstance(exp, list) and exp and all(isinstance(x, str) for x in exp)):
            return "expected must be a string or non-empty list of strings"
    if check == "constraint":
        if not isinstance(rec["constraints"], list):
            return "constraints must be a list"
        for i, spec in enumerate(rec["constraints"]):
            if not isinstance(spec, dict) or not isinstance(spec.get("type"), str):
                return f"constraint {i} must be an object with a string type"
            if spec["type"] not in VALID_CONSTRAINTS:
                return f"constraint {i} unknown type: {spec['type']!r}"
            if "value" not in spec and spec["type"] not in ("no_code_blocks",
                                                            "json_only"):
                return f"constraint {i} ({spec['type']}) missing value"
    return None


def load_cases(path: Path = CASES) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"FAIL: cases file missing: {path}")
    rows = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"FAIL: line {i} is not valid JSON: {exc}")
    return rows


# --------------------------------------------------------------------------
# scoring helpers
# --------------------------------------------------------------------------

CODE_START_RE = re.compile(
    r"^\s*(?:async\s+)?(?:def |class |import |from |@[\w.]|if __name__|"
    r"#include|public |private |function |const |let |var |int main|SELECT )")


def _looks_like_code(line: str) -> bool:
    """Is this line plausibly part of a code block (vs trailing prose)?"""
    if not line.strip():
        return True
    if line.startswith((" ", "\t")):
        return True
    if re.match(r"^\s*[-*•]\s", line):          # bullet prose after the code
        return False
    return bool(re.search(
        r"[:=()\[\]{}]|^(return|else|elif|except|finally|pass|break|continue|"
        r"yield|raise|if|for|while|throw|catch|import|from)\b", line.strip()))


def extract_code(text: str) -> str:
    """Pull the implementation out of a model response.

    When there is no fence, the model often wrapped the code in prose
    ("Thought: ... Complete Code:"). Executing the whole response then
    raises SyntaxError on the prose and hides whether the code itself
    works - so fall back to the longest code-looking run instead.
    Returns "" when the response contains no code at all.
    """
    blocks = FENCE_RE.findall(text)
    if blocks:
        return max(blocks, key=len).strip()
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if CODE_START_RE.match(ln)), None)
    if start is None:
        return ""
    kept = []
    for ln in lines[start:]:
        if kept and not _looks_like_code(ln):
            break
        kept.append(ln)
    return "\n".join(kept).strip()


def parse_json_from(text: str):
    """Return the first JSON value embedded in text, or None."""
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "{[":
            try:
                obj, _ = dec.raw_decode(text, i)
                return obj
            except Exception:
                continue
    return None


def run_assertions(code: str, assertions: list[str], timeout: float = 15.0):
    """Execute extracted code plus assertions in a subprocess."""
    program = code.rstrip() + "\n\n" + "\n".join(assertions) + "\n"
    try:
        proc = subprocess.run(
            [sys.executable, "-c", program],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout"
    if proc.returncode == 0:
        return True, "ok"
    err = (proc.stderr or proc.stdout or "").strip().splitlines()
    return False, (err[-1][:200] if err else "assertion failed")


def schema_errors(value, schema, path="$") -> list[str]:
    """Minimal JSON Schema validator (no external deps)."""
    if not isinstance(schema, dict):
        return []
    errs: list[str] = []
    stype = schema.get("type")

    if stype == "object":
        if not isinstance(value, dict):
            return [f"{path}: expected object"]
        for key in schema.get("required", []):
            if key not in value:
                errs.append(f"{path}: missing required key {key!r}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errs.append(f"{path}: unexpected key {key!r}")
        for key, sub in props.items():
            if key in value:
                errs += schema_errors(value[key], sub, f"{path}.{key}")
    elif stype == "array":
        if not isinstance(value, list):
            return [f"{path}: expected array"]
        if "minItems" in schema and len(value) < schema["minItems"]:
            errs.append(f"{path}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errs.append(f"{path}: more than {schema['maxItems']} items")
        if isinstance(schema.get("items"), dict):
            for i, item in enumerate(value):
                errs += schema_errors(item, schema["items"], f"{path}[{i}]")
    elif stype == "string":
        if not isinstance(value, str):
            return [f"{path}: expected string"]
        if "minLength" in schema and len(value) < schema["minLength"]:
            errs.append(f"{path}: shorter than {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errs.append(f"{path}: longer than {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errs.append(f"{path}: does not match pattern {schema['pattern']!r}")
    elif stype == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            return [f"{path}: expected integer"]
    elif stype == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return [f"{path}: expected number"]
    elif stype == "boolean":
        if not isinstance(value, bool):
            return [f"{path}: expected boolean"]

    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: not one of {schema['enum']}")
    if "minimum" in schema and isinstance(value, (int, float)) and value < schema["minimum"]:
        errs.append(f"{path}: below minimum {schema['minimum']}")
    if "maximum" in schema and isinstance(value, (int, float)) and value > schema["maximum"]:
        errs.append(f"{path}: above maximum {schema['maximum']}")
    return errs


def count_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def check_constraint(kind: str, text: str, spec: dict):
    if kind == "max_words":
        n = count_words(text)
        return n <= spec["value"], f"{n}/{spec['value']} words"
    if kind == "json_only":
        try:
            json.loads(text.strip())
            return True, "valid json"
        except Exception as exc:
            return False, f"not valid json: {exc}"
    if kind == "json_array_len":
        obj = parse_json_from(text)
        if not isinstance(obj, list):
            return False, "not a json array"
        ok = len(obj) == spec["value"]
        return ok, f"len={len(obj)} want={spec['value']}"
    if kind == "json_array_sum":
        obj = parse_json_from(text)
        if not isinstance(obj, list) or not all(isinstance(x, int) and not isinstance(x, bool) for x in obj):
            return False, "not an array of integers"
        total = sum(obj)
        ok = total == spec["value"]
        return ok, f"sum={total} want={spec['value']}"
    if kind == "json_object_keys":
        obj = parse_json_from(text)
        if not isinstance(obj, dict):
            return False, "not a json object"
        want = set(spec["value"])
        got = set(obj)
        ok = want == got
        return ok, f"keys={sorted(got)} want={sorted(want)}"
    if kind == "bullet_count":
        n = len([l for l in text.splitlines() if re.match(r"^\s*[-*•]\s+", l)])
        ok = n == spec["value"]
        return ok, f"bullets={n} want={spec['value']}"
    if kind == "no_code_blocks":
        ok = "```" not in text
        return ok, "no code fences" if ok else "contains code fence"
    if kind == "min_words":
        n = count_words(text)
        return n >= spec["value"], f"{n}>={spec['value']} words"
    if kind == "forbidden":
        pats = spec["value"]
        if isinstance(pats, str):
            pats = [pats]
        for pat in pats:
            if re.search(pat, text, re.I):
                return False, f"forbidden matched {pat!r}"
        return True, "no forbidden patterns"
    if kind == "required":
        pats = spec["value"]
        if isinstance(pats, str):
            pats = [pats]
        missing = [p for p in pats if not re.search(p, text, re.I)]
        if missing:
            return False, f"missing {missing[0]!r}"
        return True, "all required present"
    return False, f"unknown constraint {kind!r}"


# --------------------------------------------------------------------------
# per-check scoring
# --------------------------------------------------------------------------

def score(case: dict, response: str) -> tuple[bool, str]:
    check = case["check"]

    if check == "tests":
        code = extract_code(response)
        if not code:
            return False, "no code in response"
        return run_assertions(code, case["assertions"])

    if check == "jsonschema":
        obj = parse_json_from(response)
        if obj is None:
            return False, "no json found"
        errs = schema_errors(obj, case["schema"])
        return (not errs, "valid" if not errs else "; ".join(errs[:3]))

    if check == "exact-match":
        expected = case["expected"]
        if isinstance(expected, str):
            expected = [expected]
        for exp in expected:
            if re.search(r"\b" + re.escape(exp) + r"\b", response, re.I):
                return True, f"matched {exp!r}"
        return False, f"none of {expected!r} found"

    if check == "abstain":
        for pat in case["abstain_patterns"]:
            if re.search(pat, response, re.I):
                return True, "abstained"
        for pat in case.get("fabrication_patterns", []):
            if re.search(pat, response, re.I):
                return False, "hallucinated"
        return False, "no clear abstention"

    if check == "constraint":
        details = []
        for spec in case["constraints"]:
            ok, detail = check_constraint(spec["type"], response, spec)
            details.append(f"{spec['type']}:{detail}")
            if not ok:
                return False, "; ".join(details)
        return True, "; ".join(details)

    return False, f"unknown check {check!r}"


# --------------------------------------------------------------------------
# endpoint call
# --------------------------------------------------------------------------

def call_endpoint(endpoint: str, model: str, prompt: str, timeout: float,
                  local: bool = False):
    if local:
        return local_completion(prompt, bypass_cache=True), f"local/{LOCAL_CKPT_NAME}"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 700,
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read())
    choice = payload["choices"][0]
    return choice["message"].get("content") or "", payload.get("model", model)


# local model access (imported lazily so --self-check needs no torch)
_LOCAL_EP = None
LOCAL_CKPT_NAME = "local"


def _endpoint_module():
    global _LOCAL_EP
    if _LOCAL_EP is None:
        import importlib.util
        path = HERE.parent / "serve" / "endpoint.py"   # self-locating
        spec = importlib.util.spec_from_file_location("bhajanlal_endpoint", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _LOCAL_EP = mod
    return _LOCAL_EP


def local_completion(prompt: str, bypass_cache: bool = True) -> str:
    """Generate from the local Bhajanlal checkpoint only (no upstream).

    Eval measures the real model, so the verified-response cache is bypassed by
    default. Pass bypass_cache=False to exercise the cache (integration check).
    """
    mod = _endpoint_module()
    if not mod._load_local():
        raise RuntimeError(mod._LOCAL.get("error") or "local model failed to load")
    global LOCAL_CKPT_NAME
    LOCAL_CKPT_NAME = Path(str(mod.LOCAL_CKPT)).name
    result = mod.local_completion(prompt, max_new_tokens=700,
                                 bypass_cache=bypass_cache)
    return result.get("content") or ""


# --------------------------------------------------------------------------
# modes
# --------------------------------------------------------------------------

def mode_self_check(path: Path = CASES) -> int:
    try:
        rows = load_cases(path)
    except SystemExit as exc:
        print(exc)
        return 1
    errors = [f"line {i + 1}: {e}" for i, r in enumerate(rows) if (e := validate(r))]
    if errors:
        print("FAIL:", "; ".join(errors))
        return 1
    if validate({"id": "x"}) is None:
        print("FAIL: validator accepted a bad record")
        return 1
    by_check: dict[str, int] = {}
    for r in rows:
        by_check[r["check"]] = by_check.get(r["check"], 0) + 1
    if path.resolve() == CASES.resolve():
        print(f"OK: {len(rows)} golden cases valid, validator rejects bad records")
    else:
        print(f"OK: {len(rows)} cases from {path} valid, validator rejects bad records")
    print("    " + ", ".join(f"{k}={v}" for k, v in sorted(by_check.items())))
    return 0


def mode_list(path: Path = CASES) -> int:
    for r in load_cases(path):
        print(f"{r['id']:8} {r['check']:12} {r['difficulty']:7} {r['family']}")
    return 0


def mode_run(verbose: bool, endpoint: str, model: str, timeout: float,
             local: bool = False, cases_path: Path = CASES,
             min_pass1_override: float | None = None) -> int:
    rows = load_cases(cases_path)
    bad = [r for r in rows if validate(r)]
    if bad:
        print("FAIL: invalid cases:", [r.get("id") for r in bad])
        return 1

    try:
        min_pass1 = json.loads(CONFIG.read_text())["targets"]["min_pass1"]
    except Exception:
        min_pass1 = 0.75
    if min_pass1_override is not None:
        min_pass1 = min_pass1_override

    print(f"endpoint={'LOCAL MODEL' if local else endpoint}")
    print(f"model={'local checkpoint' if local else model}")
    print(f"cases={len(rows)} ({cases_path})  target min_pass1={min_pass1}")
    print("-" * 72)

    results = []
    for case in rows:
        t0 = time.time()
        try:
            text, served_model = call_endpoint(endpoint, model, case["prompt"],
                                               timeout, local=local)
            ok, detail = score(case, text)
            err = None
        except urllib.error.HTTPError as exc:
            text, served_model, ok, detail, err = "", "", False, "http error", f"{exc.code}"
        except Exception as exc:
            text, served_model, ok, detail, err = "", "", False, "endpoint error", str(exc)[:160]
        elapsed = time.time() - t0
        results.append({
            "id": case["id"],
            "check": case["check"],
            "difficulty": case["difficulty"],
            "pass": ok,
            "detail": detail,
            "error": err,
            "elapsed_s": round(elapsed, 2),
            "served_model": served_model,
        })
        mark = "PASS" if ok else "FAIL"
        line = f"{mark}  {case['id']:8} {case['check']:12} {elapsed:5.1f}s  {detail}"
        if err:
            line += f"  [{err}]"
        print(line)
        if verbose and text:
            print("      response:", " ".join(text.split())[:300])

    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    pass1 = passed / total if total else 0.0

    print("-" * 72)
    print(f"pass@1 = {passed}/{total} = {pass1:.3f}   (target {min_pass1})")

    by_diff: dict[str, list] = {}
    for r in results:
        by_diff.setdefault(r["difficulty"], []).append(r["pass"])
    for diff in ("easy", "medium", "hard"):
        if diff in by_diff:
            vals = by_diff[diff]
            print(f"  {diff:7} {sum(vals)}/{len(vals)}")

    RESULTS_DIR.mkdir(exist_ok=True)
    if cases_path.resolve() == CASES.resolve():
        out = RESULTS_DIR / ("local_last_run.json" if local else "last_run.json")
    else:
        # suite-named results so alternate case files never clobber the
        # golden baseline (evals/list9/cases.jsonl -> local_list9_last_run.json)
        suite = cases_path.stem if cases_path.stem != "cases" else cases_path.parent.name
        out = RESULTS_DIR / f"{'local_' if local else ''}{suite}_last_run.json"
    out.write_text(json.dumps({
        "endpoint": "local" if local else endpoint,
        "model": served_model if results else model,
        "local": local,
        "pass1": pass1,
        "passed": passed,
        "total": total,
        "min_pass1": min_pass1,
        "target_met": pass1 >= min_pass1,
        "results": results,
    }, indent=2))
    print(f"results -> {out}")

    if any(r["error"] for r in results) and passed == 0:
        print("FAIL: endpoint unreachable")
        return 1
    if pass1 < min_pass1:
        print(f"FAIL: pass@1 {pass1:.3f} below target {min_pass1}")
        return 1
    print("OK: target met")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Bhajanlal eval harness")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--self-check", action="store_true",
                      help="validate the golden case file (default)")
    mode.add_argument("--run", action="store_true",
                      help="score every case against the endpoint")
    mode.add_argument("--list", action="store_true",
                      help="print case ids and checks")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--local", action="store_true",
                    help="score the local checkpoint instead of the endpoint")
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--timeout", type=float, default=90.0)
    ap.add_argument("--cases", default=None, metavar="PATH",
                    help="case file to use (default: golden/cases.jsonl)")
    ap.add_argument("--min-pass1", type=float, default=None, metavar="F",
                    help="override the config min_pass1 target for this run")
    args = ap.parse_args()

    cases_path = Path(args.cases) if args.cases else CASES
    if args.list:
        return mode_list(cases_path)
    if args.run:
        return mode_run(args.verbose, args.endpoint, args.model, args.timeout,
                        local=args.local, cases_path=cases_path,
                        min_pass1_override=args.min_pass1)
    return mode_self_check(cases_path)


if __name__ == "__main__":
    sys.exit(main())
