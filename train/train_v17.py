#!/usr/bin/env python3
"""Bhajanlal v17 (self-learning cycle): LoRA fine-tune on v17 data.

v12-v16 all failed the entropy gate (collapse to 0.002-0.020) because the
base model memorized the small, repetitive SFT set. v17 widens the data
(293 deduped samples spanning v16 + extra + v10) and softens the recipe:
fewer epochs, lower LR, higher dropout, weight decay, label smoothing, and a
longer warmup, so the model learns without collapsing to a single token.
Recipe keeps r=16 (smaller capacity = less memorization).
"""
from __future__ import annotations

import os
os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.0")
import importlib.util
import json
import math
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "train"
CKPT = TRAIN / "checkpoints" / "bhajanlal-v17-adapter"
FINAL = TRAIN / "checkpoints" / "bhajanlal"
FINAL_NEW = TRAIN / "checkpoints" / "bhajanlal-new"
REJECTED = TRAIN / "checkpoints" / "rejected"
DATA = TRAIN / "data_v17.jsonl"
BASE_CKPT = FINAL
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
CACHE = Path.home() / ".cache" / "huggingface"

def _load_endpoint_module():
    spec = importlib.util.spec_from_file_location("bhajanlal_endpoint", ROOT / "serve" / "endpoint.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_EP = _load_endpoint_module()
# Shorter system prompt (perf: shorter prompt = less truncation + faster training).
_STYLE = ("You are Bhajanlal, a fast, precise coding assistant. "
          "Reply with runnable code in a single fenced block. "
          "Abstain plainly when unsure.")

EPOCHS = 2
BATCH = 1
GRAD_ACCUM = 2
LR = 1e-4
WARMUP_RATIO = 0.1
WEIGHT_DECAY = 0.01
LABEL_SMOOTHING = 0.05
MAX_SEQ_LEN = 128

MIN_MEAN_TOKEN_ACC = 0.20
MIN_ENTROPY = 0.03
MAX_FINAL_LOSS = 5.0


def load_samples():
    out = []
    for line in DATA.read_text().splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    seen = set(); uniq = []
    for s in out:
        key = (s["instruction"], s["response"])
        if key in seen:
            continue
        seen.add(key); uniq.append(s)
    return uniq


def validate_run(final: dict, model, tokenizer, device) -> list[str]:
    problems = []
    acc = final.get("mean_token_accuracy")
    try:
        acc = float(acc)
    except (TypeError, ValueError):
        acc = None
    if acc is None or not math.isfinite(acc):
        problems.append(f"mean_token_accuracy is not finite: {acc!r}")
    elif acc < MIN_MEAN_TOKEN_ACC:
        problems.append(f"mean_token_accuracy {acc:.4f} < {MIN_MEAN_TOKEN_ACC}")
    ent = final.get("entropy")
    try:
        ent = float(ent)
    except (TypeError, ValueError):
        ent = None
    if ent is None or not math.isfinite(ent):
        problems.append(f"entropy is not finite (NaN/diverged): {ent!r}")
    elif ent < MIN_ENTROPY:
        problems.append(f"entropy {ent:.4f} < {MIN_ENTROPY} (collapsed)")
    loss = final.get("train_loss", final.get("loss"))
    try:
        loss = float(loss)
    except (TypeError, ValueError):
        loss = None
    if loss is None or not math.isfinite(loss):
        problems.append(f"train_loss is not finite: {loss!r}")
    elif loss > MAX_FINAL_LOSS:
        problems.append(f"train_loss {loss:.4f} > {MAX_FINAL_LOSS}")

    try:
        msgs = [{"role": "system", "content": _STYLE},
                {"role": "user", "content": "Write a Python function to reverse a string. Return ONLY the function in a code block."}]
        text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        if not text:
            problems.append("chat template rendered empty smoke prompt")
        else:
            import torch
            dev = device
            enc = tokenizer(text, return_tensors="pt", truncation=True, max_length=MAX_SEQ_LEN).to(dev)
            with torch.inference_mode():
                out = model.generate(**enc, max_new_tokens=64, do_sample=False,
                                     pad_token_id=tokenizer.eos_token_id, use_cache=True)
            gen = tokenizer.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()
            if not gen:
                problems.append("smoke generation returned empty output")
            elif "```" not in gen and "{" not in gen:
                problems.append(f"smoke generation leaked template markup: {gen[:80]!r}")
    except Exception as exc:
        problems.append(f"smoke generation failed: {exc}")
    return problems


def quarantine(reason: str) -> Path | None:
    if not CKPT.exists() or not any(CKPT.iterdir()):
        return None
    REJECTED.mkdir(parents=True, exist_ok=True)
    dest = REJECTED / f"{CKPT.name}-{time.strftime('%Y%m%d-%H%M%S')}"
    shutil.move(str(CKPT), str(dest))
    (dest / "REJECTED.txt").write_text(
        f"rejected: {reason}\nat: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n"
        f"script: {Path(__file__).name}\n", encoding="utf-8")
    return dest


def main():
    import fcntl
    TRAIN.mkdir(parents=True, exist_ok=True)
    lock_path = TRAIN / ".train_v17.lock"
    lock_fh = open(lock_path, "w")
    try:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (BlockingIOError, OSError):
        print("=== another train_v17.py instance is already running; exiting ===",
              flush=True)
        sys.exit(0)
    lock_fh.write(str(__import__("os").getpid()))
    lock_fh.flush()
    samples = load_samples()
    print(f"=== Bhajanlal v17 training -> {CKPT.name} ({len(samples)} samples) ===", flush=True)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model
    from datasets import Dataset
    from trl import SFTTrainer, SFTConfig

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device} | torch {torch.__version__}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(str(BASE_CKPT), cache_dir=str(CACHE))
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        str(BASE_CKPT), cache_dir=str(CACHE), torch_dtype=torch.float16,
        trust_remote_code=True)
    model.to(device)
    torch.set_float32_matmul_precision("high")

    lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.2, bias="none",
                      task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                      "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    def fmt(s):
        msgs = [
            {"role": "system", "content": _STYLE},
            {"role": "user", "content": s["instruction"]},
            {"role": "assistant", "content": s["response"]},
        ]
        text = tokenizer.apply_chat_template(msgs, tokenize=False)
        if not text:
            raise RuntimeError("chat template produced empty text")
        return text

    ds = Dataset.from_dict({"text": [fmt(s) for s in samples]})

    args = SFTConfig(output_dir=str(CKPT), num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH, gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LR, warmup_ratio=WARMUP_RATIO, lr_scheduler_type="cosine",
        weight_decay=WEIGHT_DECAY, label_smoothing_factor=LABEL_SMOOTHING,
        logging_steps=5, save_strategy="steps", save_steps=50, fp16=False, bf16=False,
        dataset_text_field="text", max_length=MAX_SEQ_LEN, packing=False,
        report_to="none", dataloader_num_workers=0, dataloader_pin_memory=False)
    trainer = SFTTrainer(model=model, args=args, train_dataset=ds, processing_class=tokenizer)

    # Resume from a partial checkpoint if one exists (e.g. after a crash/restart).
    resume_ckpt = None
    if CKPT.exists():
        ckpts = sorted(CKPT.glob("checkpoint-*"), key=lambda p: int(p.name.split("-")[-1]))
        if ckpts:
            resume_ckpt = str(ckpts[-1])
    print("Training..." + (f" (resuming from {resume_ckpt})" if resume_ckpt else ""), flush=True)
    t0 = time.time()
    trainer.train(resume_from_checkpoint=resume_ckpt)
    dur = time.time() - t0

    history = trainer.state.log_history or []
    metric_entries = [e for e in history if "mean_token_accuracy" in e]
    tr = metric_entries[-1] if metric_entries else (history[-1] if history else {})
    print("log_history entries:", len(history), "metric-bearing:", len(metric_entries), flush=True)
    if metric_entries:
        print("last metrics:", {k: metric_entries[-1].get(k) for k in
              ("loss", "entropy", "mean_token_accuracy", "train_loss")}, flush=True)
    if "train_loss" not in tr and "loss" in tr:
        tr = dict(tr)
        tr["train_loss"] = tr["loss"]
    print("Validating run...", flush=True)
    problems = validate_run(tr, model, tokenizer, device)

    meta = {"base_model": str(BASE_CKPT), "method": "LoRA (r=16, alpha=32, 7 modules) on bhajanlal, LR=1e-4, epochs=2, dropout=0.2, weight_decay=0.01, label_smoothing=0.05 (v17)",
            "device": device, "epochs": EPOCHS, "samples": len(samples),
            "checkpoint": str(CKPT), "train_seconds": round(dur, 1), "final": tr}

    if problems:
        reason = "; ".join(problems)
        dest = quarantine(reason)
        meta.update({"status": "failed", "problems": problems,
                     "quarantined_to": str(dest) if dest else None, "usable": False})
        (TRAIN / "metadata_v17.json").write_text(json.dumps(meta, indent=2))
        print(f"=== v17 training FAILED validation ===", flush=True)
        for p in problems:
            print(f"  FAIL: {p}", flush=True)
        print(f"checkpoint quarantined -> {dest}", flush=True)
        sys.exit(1)

    model.save_pretrained(str(CKPT))
    tokenizer.save_pretrained(str(CKPT))
    meta.update({"status": "adapter_ok", "problems": [], "usable": False,
                 "gates": {"min_mean_token_accuracy": MIN_MEAN_TOKEN_ACC,
                           "min_entropy": MIN_ENTROPY, "max_final_loss": MAX_FINAL_LOSS}})
    (TRAIN / "metadata_v17.json").write_text(json.dumps(meta, indent=2))
    print(f"=== v17 adapter trained in {dur/60:.1f} min; merging into dense model ===", flush=True)

    base = AutoModelForCausalLM.from_pretrained(
        str(BASE_CKPT), cache_dir=str(CACHE), torch_dtype=torch.float16,
        trust_remote_code=True)
    from peft import PeftModel
    merged_model = PeftModel.from_pretrained(base, str(CKPT))
    merged_model = merged_model.merge_and_unload()
    merged_model.eval()

    if FINAL_NEW.exists():
        shutil.rmtree(FINAL_NEW)
    FINAL_NEW.mkdir(parents=True, exist_ok=True)
    merged_model.half().save_pretrained(str(FINAL_NEW), safe_serialization=True)
    tokenizer.save_pretrained(str(FINAL_NEW))

    print("Smoke-testing merged dense model...", flush=True)
    device2 = "cpu"
    merged_model.to(device2)
    msgs = [{"role": "system", "content": _STYLE},
            {"role": "user", "content": "Write a Python function to reverse a string. Return ONLY the function in a code block."}]
    prompt = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    enc = tokenizer(prompt, return_tensors="pt").to(device2)
    with torch.inference_mode():
        out = merged_model.generate(**enc, max_new_tokens=64, do_sample=False,
                                    pad_token_id=tokenizer.eos_token_id, use_cache=True)
    text = tokenizer.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    print(f"smoke output: {text[:200]!r}", flush=True)
    if not text or "```" not in text:
        reason = f"merged model smoke failed: {text[:120]!r}"
        shutil.rmtree(FINAL_NEW, ignore_errors=True)
        meta.update({"status": "failed", "problems": [reason], "usable": False})
        (TRAIN / "metadata_v17.json").write_text(json.dumps(meta, indent=2))
        print(f"FAIL: {reason}", flush=True)
        sys.exit(1)

    backup = REJECTED / f"bhajanlal-pre-v17-{time.strftime('%Y%m%d-%H%M%S')}"
    REJECTED.mkdir(parents=True, exist_ok=True)
    shutil.move(str(FINAL), str(backup))
    shutil.move(str(FINAL_NEW), str(FINAL))

    meta.update({"status": "ok", "problems": [], "usable": True,
                 "final_checkpoint": str(FINAL),
                 "backup": str(backup),
                 "gates": {"min_mean_token_accuracy": MIN_MEAN_TOKEN_ACC,
                           "min_entropy": MIN_ENTROPY, "max_final_loss": MAX_FINAL_LOSS}})
    (TRAIN / "metadata_v17.json").write_text(json.dumps(meta, indent=2))
    print(f"=== v17 promoted -> {FINAL} (backup {backup}) ===", flush=True)


if __name__ == "__main__":
    main()
