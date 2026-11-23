#!/usr/bin/env python3
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
