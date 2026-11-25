#!/usr/bin/env python3
"""Build a large deduped training set from all existing data files."""
import json
from pathlib import Path

TRAIN = Path(__file__).resolve().parent
SOURCES = [
    "data.jsonl", "data_large.jsonl", "data_max.jsonl", "data_extra.jsonl",
    "data_diverse.jsonl", "data_beam_free.jsonl",
    "data_v6.jsonl", "data_v7.jsonl", "data_v8.jsonl", "data_v9.jsonl",
    "data_v10.jsonl", "data_v11.jsonl", "data_v12.jsonl", "data_v13.jsonl",
    "data_v14.jsonl", "data_v15.jsonl", "data_v16.jsonl", "data_v17.jsonl",
]
OUT = TRAIN / "data_big.jsonl"

seen = set()
rows = []
for name in SOURCES:
    p = TRAIN / name
    if not p.exists():
        continue
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        key = (rec.get("instruction"), rec.get("response"))
        if key in seen:
            continue
        seen.add(key)
        rows.append(rec)

OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
print(f"wrote {len(rows)} unique samples to {OUT}")
