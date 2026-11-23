#!/usr/bin/env python3
"""Bhajanlal inference: load the merged model (bhajanlal-pro-max) and generate."""
import json, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CKPT = ROOT / "train" / "checkpoints" / "bhajanlal-pro-max-2"
BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
CACHE = Path.home() / ".cache" / "huggingface"

_model = None
_tokenizer = None


def load_model():
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    _tokenizer = AutoTokenizer.from_pretrained(str(CKPT), cache_dir=str(CACHE))
    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token
    if (CKPT / "adapter_config.json").exists():
        # legacy path: LoRA adapter over the base model
        from peft import PeftModel
        base = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL, cache_dir=str(CACHE), torch_dtype=torch.float16
        )
        _model = PeftModel.from_pretrained(base, str(CKPT))
        _model = _model.merge_and_unload()
    else:
        # dense merged checkpoint (bhajanlal-pro-max)
        _model = AutoModelForCausalLM.from_pretrained(
            str(CKPT), torch_dtype=torch.float16
        )
    _model.to(device)
    _model.eval()
    print(f"[inference] {CKPT.name} loaded on {device}", flush=True)
    return _model, _tokenizer


def generate(prompt: str, max_new_tokens: int = 256) -> str:
    import torch
    model, tokenizer = load_model()
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    text = ("### Instruction:\nYou are Bhajanlal, a fast, precise coding assistant. "
            "Give a short explanation of why the approach works before the code, "
            "then provide complete, runnable code.\n\n"
            f"{prompt}\n\n### Response:\n")
    inputs = tokenizer(text, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    result = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    return result.strip()


if __name__ == "__main__":
    # CLI test
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "Write a Python function to reverse a string."
    print(f"Prompt: {prompt}")
    print(f"Response: {generate(prompt)}")
    meta_path = ROOT / "train" / "checkpoints" / "bhajanlal-pro-max-2" / "metadata.json"
    meta = json.loads(meta_path.read_text())
    print(f"\nModel: {meta['model_name']} (merged from 4 LoRAs over {meta['base_model']}, "
          f"fp16 dense)")
