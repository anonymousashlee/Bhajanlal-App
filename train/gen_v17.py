import json, random
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "train"
OUT = TRAIN / "data_v17.jsonl"
random.seed(7)
rows = []
for name in ("data_v16.jsonl",):
    p = TRAIN / name
    if p.exists():
        for line in p.read_text().splitlines():
            line=line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
def parse_jsonl_multi(path):
    txt = path.read_text()
    dec = json.JSONDecoder()
    i=0; out=[]; n=len(txt)
    while i<n:
        while i<n and txt[i].isspace(): i+=1
        if i>=n: break
        try:
            obj,end=dec.raw_decode(txt,i); out.append(obj); i=end
        except json.JSONDecodeError:
            i+=1
    return out
p = TRAIN / "data_extra.jsonl"
if p.exists():
    extra = parse_jsonl_multi(p)
    random.shuffle(extra)
    rows += extra[:120]
p = TRAIN / "data_v10.jsonl"
if p.exists():
    v10 = parse_jsonl_multi(p)
    random.shuffle(v10)
    rows += v10[:60]
seen=set(); uniq=[]
for r in rows:
    key=(r["instruction"], r["response"])
    if key in seen: continue
    seen.add(key); uniq.append(r)
OUT.write_text("\n".join(json.dumps(r) for r in uniq)+"\n")
print(f"wrote {len(uniq)} unique samples -> {OUT}")
