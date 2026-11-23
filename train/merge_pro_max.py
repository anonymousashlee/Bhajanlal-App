#!/usr/bin/env python3
"""Compile every Bhajanlal LoRA checkpoint into one model: bhajanlal-pro-max-2.

Sources (all LoRA r=16, alpha=32, q_proj/v_proj on Qwen/Qwen2.5-0.5B-Instruct):
  - bhajanlal-v1        (root adapter, final step 30,  loss 0.5023)
  - bhajanlal-v2        (root adapter, final step 252, loss 0.3271)
  - bhajanlal-v3        (checkpoint-168,               loss 0.3480)
  - bhajanlal-v4        (root adapter, final step 336, loss 0.2484)

Method: load base -> attach all 4 adapters -> SVD-projected equal-weight merge
(every Bhajanlal fine-tune contributes exactly 1/4) -> merge the combined
adapter into the base weights -> save one dense model + tokenizer + metadata.
Source adapters are deleted from disk afterwards; this model is the single
surviving artifact.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CKPTS = ROOT / "train" / "checkpoints"
OUT = CKPTS / "bhajanlal-pro-max-2"
BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
CACHE = Path.home() / ".cache" / "huggingface"

# (adapter name, path, final training loss)
SOURCES = [
    ("v1", CKPTS / "bhajanlal-v1", 0.5023),
    ("v2", CKPTS / "bhajanlal-v2", 0.3271),
    ("v3", CKPTS / "bhajanlal-v3" / "checkpoint-168", 0.3480),
    ("v4", CKPTS / "bhajanlal-v4", 0.2484),
]
# Equal-weight combination: every Bhajanlal fine-tune contributes exactly 1/4.
WEIGHTS = [0.25, 0.25, 0.25, 0.25]
MERGED_RANK = 16


def main() -> None:
    t0 = time.time()
    for _, path, _ in SOURCES:
        if not (path / "adapter_model.safetensors").exists():
            raise SystemExit(f"missing adapter: {path}")

    weights = list(WEIGHTS)
    if len(weights) != len(SOURCES) or abs(sum(weights) - 1.0) > 1e-6:
        raise SystemExit("WEIGHTS must sum to 1.0 and match SOURCES")
    print("merge weights:", {n: round(w, 4) for (n, _, _), w in zip(SOURCES, weights)})

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    tok = AutoTokenizer.from_pretrained(BASE_MODEL, cache_dir=str(CACHE))
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, cache_dir=str(CACHE), torch_dtype=torch.float32
    )  # fp32 for numerically stable SVD merge on CPU

    model = PeftModel.from_pretrained(
        base, str(SOURCES[0][1]), adapter_name=SOURCES[0][0], is_trainable=False
    )
    for name, path, _ in SOURCES[1:]:
        model.load_adapter(str(path), adapter_name=name, is_trainable=False)
        print(f"loaded adapter {name} <- {path}")

    model.add_weighted_adapter(
        adapters=[n for n, _, _ in SOURCES],
        weights=weights,
        adapter_name="promax",
        combination_type="svd",
        svd_rank=MERGED_RANK,
    )
    print("combined adapters -> 'promax' (SVD-projected to rank", MERGED_RANK, ")")

    model.set_adapter("promax")
    merged = model.merge_and_unload(adapter_names=["promax"])
    merged.eval()

    OUT.mkdir(parents=True, exist_ok=True)
    merged.half().save_pretrained(str(OUT), safe_serialization=True)
    tok.save_pretrained(str(OUT))

    meta = {
        "model_name": "bhajanlal-pro-max-2",
        "base_model": BASE_MODEL,
        "method": "4-way equal-weight LoRA merge (SVD, rank 16) -> dense fp16",
        "lora_r": MERGED_RANK,
        "lora_alpha": 32,
        "target_modules": ["q_proj", "v_proj"],
        "sources": [
            {"adapter": n, "path": str(p), "final_loss": l, "weight": round(w, 4)}
            for (n, p, l), w in zip(SOURCES, weights)
        ],
        "merged_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "merge_seconds": round(time.time() - t0, 1),
        "excluded": [
            "train/checkpoint.safetensors (byte-level TinyGPT POC, incompatible architecture) - deleted after merge",
            "train/checkpoints/bhajanlal-v5 (empty, never trained) - deleted",
            "source adapters bhajanlal-v1..v4 and bhajanlal-pro-max (v1) - deleted after merge",
        ],
    }
    (OUT / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"saved -> {OUT} ({(OUT / 'model.safetensors').stat().st_size / 1e6:.0f} MB)")
    print(f"done in {meta['merge_seconds']}s")


if __name__ == "__main__":
    main()
