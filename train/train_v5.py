#!/usr/bin/env python3
"""Bhajanlal v5: higher-quality LoRA fine-tune."""
from __future__ import annotations

import json, math, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "train"
CKPT = TRAIN / "checkpoints" / "bhajanlal-v5"
REJECTED = TRAIN / "checkpoints" / "rejected"
DATA_FILES = [TRAIN / "data_max.jsonl", TRAIN / "data_extra.jsonl"]
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
CACHE = Path.home() / ".cache" / "huggingface"

EPOCHS = 3
BATCH = 1
GRAD_ACCUM = 8
LR = 1e-4
WARMUP_RATIO = 0.05
MAX_SEQ_LEN = 512

# --- post-training acceptance gates -----------------------------------------
# Calibrated against real runs: v4 (healthy) -> entropy 0.408, acc 0.935,
# loss 0.441. v5 (broken) -> entropy NaN, acc 0.000, loss 0.386. Loss alone
# cannot tell them apart, so entropy and token accuracy are the real gates.
MIN_MEAN_TOKEN_ACC = 0.30   # v4=0.935, v5=0.000
MIN_ENTROPY = 0.05          # v4=0.408, v5=NaN (collapse or divergence)
MAX_FINAL_LOSS = 2.0        # sanity ceiling; NaN/inf caught by isfinite

def load_samples():
    out = []
    for f in DATA_FILES:
        if f.exists():
            for line in f.read_text().splitlines():
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    seen = set(); uniq = []
    for s in out:
        key = s.get("instruction", "")
        if key in seen: continue
        seen.add(key); uniq.append(s)
    return uniq

def validate_run(final: dict, model, tokenizer, device) -> list[str]:
    """Return a list of problems. Empty list == the run is shippable.

    Checks, in order of how often they actually catch a broken run:
      1. mean token accuracy  (v5's real failure: 0.0)
      2. entropy finite & sane (v5's loud symptom: NaN)
      3. loss finite (a NaN loss poisons the weights even when loss "looks" low)
      4. smoke generation      (template actually applied, model actually talks)
    """
    problems = []
    acc = final.get("mean_token_accuracy")
    if not isinstance(acc, (int, float)) or not math.isfinite(acc):
        problems.append(f"mean_token_accuracy is not finite: {acc!r}")
    elif acc < MIN_MEAN_TOKEN_ACC:
        problems.append(f"mean_token_accuracy {acc:.4f} < {MIN_MEAN_TOKEN_ACC} "
                        f"(model learned nothing usable)")

    ent = final.get("entropy")
    if not isinstance(ent, (int, float)) or not math.isfinite(ent):
        problems.append(f"entropy is not finite (NaN/diverged): {ent!r}")
    elif ent < MIN_ENTROPY:
        problems.append(f"entropy {ent:.4f} < {MIN_ENTROPY} (collapsed: "
                        f"model emits one token regardless of input)")

    loss = final.get("train_loss")
    if not isinstance(loss, (int, float)) or not math.isfinite(loss):
        problems.append(f"train_loss is not finite: {loss!r}")
    elif loss > MAX_FINAL_LOSS:
        problems.append(f"train_loss {loss:.4f} > {MAX_FINAL_LOSS}")

    # Smoke test: does a prompt rendered through the real chat template come
    # back as an answer rather than raw template text or an empty string?
    try:
        msgs = [{"role": "user", "content": "Reply with exactly: OK"}]
        prompt = tokenizer.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=True)
        if not prompt:
            problems.append("chat template rendered empty smoke prompt")
        else:
            import torch
            enc = tokenizer(prompt, return_tensors="pt").to(device)
            with torch.inference_mode():
                out = model.generate(
                    **enc, max_new_tokens=16, do_sample=False,
                    pad_token_id=tokenizer.eos_token_id, use_cache=True)
            text = tokenizer.decode(
                out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()
            if not text:
                problems.append("smoke generation returned empty output")
            elif "<|im_start|>" in text or "### Instruction" in text:
                problems.append(f"smoke generation leaked template markup: {text[:80]!r}")
    except Exception as exc:
        problems.append(f"smoke generation failed: {exc}")
    return problems


def quarantine(reason: str) -> Path | None:
    """Move a bad checkpoint out of the load path so nothing can pick it up.

    Returns the new location, or None if there was nothing to move.
    """
    if not CKPT.exists() or not any(CKPT.iterdir()):
        return None
    REJECTED.mkdir(parents=True, exist_ok=True)
    dest = REJECTED / f"{CKPT.name}-{time.strftime('%Y%m%d-%H%M%S')}"
    shutil.move(str(CKPT), str(dest))
    (dest / "REJECTED.txt").write_text(
        f"rejected: {reason}\nat: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n"
        f"script: {Path(__file__).name}\n",
        encoding="utf-8")
    return dest


def main():
    TRAIN.mkdir(parents=True, exist_ok=True)
    samples = load_samples()
    print(f"=== Bhajanlal v5 training -> {CKPT.name} ({len(samples)} samples) ===", flush=True)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model
    from datasets import Dataset
    from trl import SFTTrainer, SFTConfig

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device} | torch {torch.__version__}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, cache_dir=str(CACHE))
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, cache_dir=str(CACHE), torch_dtype=torch.float16)
    model.gradient_checkpointing_enable()
    model.to(device)

    lora = LoraConfig(r=32, lora_alpha=64, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
                      target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    def fmt(s):
        msgs = [
            {"role":"system","content":"You are Bhajanlal, a fast precise coding assistant. Be concise; prefer runnable code."},
            {"role":"user","content":s["instruction"]},
            {"role":"assistant","content":s["response"]},
        ]
        # No silent fallback. The old alpaca-format except branch trained on a
        # different format than the model's chat template, which is how a run can
        # "succeed" while producing an unusable adapter. If the template breaks,
        # stop and say so.
        try:
            text = tokenizer.apply_chat_template(msgs, tokenize=False)
        except Exception as exc:
            raise RuntimeError(
                f"apply_chat_template failed on sample {s.get('instruction','')[:60]!r}: {exc}. "
                "Refusing to train on a fallback format."
            ) from exc
        if not text or "<|im_start|>user" not in text:
            raise RuntimeError(
                "chat template produced empty or unmarked text - refusing to train. "
                "The tokenizer likely has no chat template for this model."
            )
        return text

    ds = Dataset.from_dict({"text": [fmt(s) for s in samples]})

    args = SFTConfig(output_dir=str(CKPT), num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH, gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LR, warmup_ratio=WARMUP_RATIO, lr_scheduler_type="cosine",
        logging_steps=10, save_strategy="epoch", fp16=False, bf16=False,
        dataset_text_field="text", max_length=MAX_SEQ_LEN, packing=False,
        report_to="none")
    trainer = SFTTrainer(model=model, args=args, train_dataset=ds, processing_class=tokenizer)

    print("Training...", flush=True)
    t0 = time.time()
    trainer.train()
    dur = time.time() - t0

    tr = trainer.state.log_history[-1] if trainer.state.log_history else {}
    # NOTE: save_strategy="epoch" already wrote into CKPT during training, so a
    # broken run leaves real files behind. Validate first; only a passing run
    # gets promoted to a final adapter + a status=ok metadata file.
    print("Validating run...", flush=True)
    problems = validate_run(tr, model, tokenizer, device)

    meta = {"base_model":MODEL_ID,"method":"LoRA (r=32, alpha=64, 7 modules)","device":device,
            "epochs":EPOCHS,"samples":len(samples),"checkpoint":str(CKPT),
            "train_seconds":round(dur,1),"final":tr}

    if problems:
        reason = "; ".join(problems)
        dest = quarantine(reason)
        meta.update({"status": "failed",
                     "problems": problems,
                     "quarantined_to": str(dest) if dest else None,
                     "usable": False})
        (TRAIN / "metadata_v5.json").write_text(json.dumps(meta, indent=2))
        print(f"=== v5 training FAILED validation ===", flush=True)
        for p in problems:
            print(f"  FAIL: {p}", flush=True)
        print(f"checkpoint quarantined -> {dest}", flush=True)
        print("NOT usable. Nothing was promoted.", flush=True)
        sys.exit(1)

    model.save_pretrained(str(CKPT))
    tokenizer.save_pretrained(str(CKPT))
    meta.update({"status": "ok", "problems": [], "usable": True,
                 "gates": {"min_mean_token_accuracy": MIN_MEAN_TOKEN_ACC,
                           "min_entropy": MIN_ENTROPY,
                           "max_final_loss": MAX_FINAL_LOSS}})
    (TRAIN / "metadata_v5.json").write_text(json.dumps(meta, indent=2))
    print(f"=== v5 training complete in {dur/60:.1f} min ===", flush=True)
    print("validation passed: "
          f"acc={tr.get('mean_token_accuracy')} "
          f"entropy={tr.get('entropy')} "
          f"loss={tr.get('train_loss')}", flush=True)

if __name__ == "__main__":
    main()
