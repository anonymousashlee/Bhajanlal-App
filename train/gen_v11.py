"""Generate data_v11.jsonl = data_v10 + verified samples from proposals 2 & 3."""
import json
from pathlib import Path

TRAIN = Path(__file__).resolve().parent
OUT = TRAIN / "data_v11.jsonl"
VERIFIED = TRAIN.parent / "selflearn" / "verified"

rows = [json.loads(l) for l in (TRAIN / "data_v10.jsonl").read_text().splitlines() if l.strip()]
before = len(rows)

for name in ("proposal-2.verified.jsonl", "proposal-3.verified.jsonl"):
    p = VERIFIED / name
    if not p.exists():
        continue
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if "instruction" in rec and "response" in rec:
            rows.append({"instruction": rec["instruction"].strip(),
                         "response": rec["response"].strip()})

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
print(f"data_v11.jsonl: {before} -> {len(rows)} samples (+{len(rows)-before} new)")
