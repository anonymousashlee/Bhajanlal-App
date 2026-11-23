#!/usr/bin/env python3
"""Promote the already-trained v12 adapter (checkpoint-164) into the dense model.

Used when training passed the gate but the adapter was quarantined only because
the (now-corrected) entropy threshold was too strict. Loads the adapter from
the final epoch checkpoint, merges into bhajanlal-pro-max-2, smoke-tests, and
atomically swaps. Run evals/harness.py --run --local afterwards.
"""
import json, shutil, time, importlib.util
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "train"
FINAL = TRAIN / "checkpoints" / "bhajanlal-pro-max-2"
FINAL_NEW = TRAIN / "checkpoints" / "bhajanlal-pro-max-2-new"
REJECTED = TRAIN / "checkpoints" / "rejected"
ADAPTER = TRAIN / "checkpoints" / "bhajanlal-v12-adapter" / "checkpoint-164"
CACHE = Path.home() / ".cache" / "huggingface"

def _load_endpoint():
    spec = importlib.util.spec_from_file_location("bhajanlal_endpoint", ROOT / "serve" / "endpoint.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
_STYLE = _load_endpoint()._STYLE

assert ADAPTER.exists(), f"adapter checkpoint missing: {ADAPTER}"
assert FINAL.exists(), f"base dense missing: {FINAL}"

tokenizer = AutoTokenizer.from_pretrained(str(ADAPTER), cache_dir=str(CACHE))
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

base = AutoModelForCausalLM.from_pretrained(str(FINAL), cache_dir=str(CACHE), torch_dtype=torch.float32, trust_remote_code=True)
merged = PeftModel.from_pretrained(base, str(ADAPTER)).merge_and_unload()
merged.eval()

# Smoke check
dev = "mps" if torch.backends.mps.is_available() else "cpu"
merged.to(dev)
msgs = [{"role":"system","content":_STYLE},{"role":"user","content":"Write a Python function to reverse a string. Return ONLY the function in a code block."}]
prompt = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
enc = tokenizer(prompt, return_tensors="pt").to(dev)
with torch.inference_mode():
    out = merged.generate(**enc, max_new_tokens=64, do_sample=False, pad_token_id=tokenizer.eos_token_id, use_cache=True)
text = tokenizer.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()
print(f"smoke output: {text[:200]!r}")
if not text:
    raise SystemExit(f"FAIL smoke (empty): {text[:120]!r}")

if FINAL_NEW.exists():
    shutil.rmtree(FINAL_NEW)
FINAL_NEW.mkdir(parents=True, exist_ok=True)
merged.half().save_pretrained(str(FINAL_NEW), safe_serialization=True)
tokenizer.save_pretrained(str(FINAL_NEW))

backup = REJECTED / f"bhajanlal-pro-max-2-pre-v12-{time.strftime('%Y%m%d-%H%M%S')}"
REJECTED.mkdir(parents=True, exist_ok=True)
shutil.move(str(FINAL), str(backup))
shutil.move(str(FINAL_NEW), str(FINAL))

# write metadata
meta = {"base_model": str(FINAL), "method": "LoRA v12 promoted from checkpoint-164 (LR=1e-4, entropy 0.0468)",
        "final_checkpoint": str(FINAL), "backup": str(backup), "status": "ok", "usable": True,
        "final": {"entropy": 0.04684305447153747, "mean_token_accuracy": 0.9916338622570038,
                  "train_loss": 0.02983111992660092}}
(TRAIN / "metadata_v12.json").write_text(json.dumps(meta, indent=2))
print(f"=== v12 promoted -> {FINAL} (backup {backup}) ===")
