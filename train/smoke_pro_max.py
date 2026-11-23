#!/usr/bin/env python3
"""Smoke test: base Qwen vs bhajanlal-pro-max vs bhajanlal-v4 (best single)."""
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CKPTS = ROOT / "train" / "checkpoints"
CACHE = Path.home() / ".cache" / "huggingface"
BASE = "Qwen/Qwen2.5-0.5B-Instruct"

PROMPTS = [
    "Write a Python function to reverse a string.",
    "Write a Python function to check if a number is prime.",
    "Write a Python function to flatten a nested list.",
    "What is the capital of France?",
    "Summarize what a hash map is in one sentence.",
]


def gen(model, tok, prompt, max_new_tokens=110):
    text = f"### Instruction:\n{prompt}\n\n### Response:\n"
    import torch
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in tok(text, return_tensors="pt").items()}
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False,
            pad_token_id=tok.pad_token_id or tok.eos_token_id,
        )
    dt = time.time() - t0
    return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True), dt


def load(path, is_lora):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    tok = AutoTokenizer.from_pretrained(str(path) if is_lora else path, cache_dir=str(CACHE))
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    src = BASE if is_lora else path
    m = AutoModelForCausalLM.from_pretrained(src, cache_dir=None if not is_lora else str(CACHE), dtype=torch.float16)
    if is_lora:
        m = PeftModel.from_pretrained(m, str(path))
        m = m.merge_and_unload()
    m.eval()
    return m, tok


def main():
    import torch
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    variants = [
        ("base", BASE, False),
        ("bhajanlal-v4", str(CKPTS / "bhajanlal-v4"), True),
        ("bhajanlal-pro-max", str(CKPTS / "bhajanlal-pro-max"), False),
    ]
    results = {}
    for name, path, is_lora in variants:
        m, tok = load(path, is_lora)
        m.to(device)
        if device == "mps":
            m = m.to(torch.float16)
        results[name] = []
        for p in PROMPTS:
            out, dt = gen(m, tok, p)
            results[name].append((p, out, dt))
        del m
        if device == "mps":
            torch.mps.empty_cache()
    for name, _, _ in variants:
        print(f"\n{'='*70}\n### {name}\n{'='*70}")
        for p, out, dt in results[name]:
            print(f"\nQ: {p}\nA ({dt:.1f}s): {out.strip()[:400]}")


if __name__ == "__main__":
    main()
