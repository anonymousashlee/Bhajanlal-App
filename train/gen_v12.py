"""Generate data_v12.jsonl = data_v11 + beam-free skill-stack Q&A (diversity).

Goal: recover from v11's entropy collapse by adding diverse, non-code
instruction/response pairs (data_beam_free.jsonl) so the model does not
over-fit to a single response template.
"""
import json
from pathlib import Path

TRAIN = Path(__file__).resolve().parent
OUT = TRAIN / "data_v12.jsonl"

rows = []
for name in ("data_v11.jsonl", "data_beam_free.jsonl"):
    p = TRAIN / name
    if not p.exists():
        continue
    for line in p.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
before = len(rows)

seen = set()
deduped = []
for r in rows:
    key = r["instruction"]
    if key in seen:
        continue
    seen.add(key)
    deduped.append(r)
rows = deduped

OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
print(f"data_v12.jsonl: {before} -> {len(rows)} samples")