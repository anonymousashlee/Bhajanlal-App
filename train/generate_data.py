#!/usr/bin/env python3
"""Generate a deterministic synthetic Python-coding corpus for the Bhajanlal
proof-of-concept training run. Produces train.txt and val.txt (byte-level).

This is deliberately small: it exists to prove the *training loop* works on
MPS, not to produce a MiMo-class model.
"""
from __future__ import annotations

import random
from pathlib import Path

HERE = Path(__file__).parent
SEED = 1337

NAMES = ["add", "subtract", "multiply", "divide", "square", "double", "triple",
         "increment", "decrement", "absolute", "negate", "clamp", "max_value",
         "min_value", "is_even", "is_positive", "sum_list", "count_items",
         "first_item", "last_item", "reverse_string", "to_upper", "length"]
OPS = ["a + b", "a - b", "a * b", "a // b", "a % b", "a ** b", "a + 1",
       "a - 1", "a * 2", "a / 2", "max(a, b)", "min(a, b)", "abs(a)"]
TYPES = ["int", "float", "str", "list"]


def snippet(rng: random.Random) -> str:
    name = rng.choice(NAMES)
    op = rng.choice(OPS)
    params = "a, b" if "b" in op else "a"
    doc = f"Return {op.replace('_', ' ')}."
    body = f"    return {op}"
    if rng.random() < 0.25:
        pre = f"    # compute {name}\n"
    else:
        pre = ""
    return f"def {name}({params}):\n    \"\"\"{doc}\"\"\"\n{pre}{body}\n"


def main() -> None:
    rng = random.Random(SEED)
    parts = [snippet(rng) for _ in range(1200)]
    text = "\n".join(parts)
    split = int(len(text) * 0.9)
    (HERE / "train.txt").write_text(text[:split], encoding="utf-8")
    (HERE / "val.txt").write_text(text[split:], encoding="utf-8")
    print(f"OK: corpus {len(text)} bytes -> train.txt ({split}B) + val.txt ({len(text)-split}B)")


if __name__ == "__main__":
    main()
