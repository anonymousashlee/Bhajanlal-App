#!/usr/bin/env python3
"""Resume Bhajanlal v3 training from checkpoint-168 to completion."""
import json, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "train"
CKPT = TRAIN / "checkpoints" / "bhajanlal-v3"
DATA = TRAIN / "data_max.jsonl"
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
CACHE = Path.home() / ".cache" / "huggingface"
RESUME = CKPT / "checkpoint-168"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from datasets import Dataset
from trl import SFTTrainer, SFTConfig

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"=== Resume v3 from {RESUME} on {device} ===", flush=True)

samples = [json.loads(l) for l in DATA.read_text().splitlines() if l.strip()]
print(f"Loaded {len(samples)} samples", flush=True)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, cache_dir=str(CACHE))
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Load base + adapter from checkpoint (resume weights)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, cache_dir=str(CACHE), torch_dtype=torch.float16
)
from peft import PeftModel
model = PeftModel.from_pretrained(model, str(RESUME))
model.gradient_checkpointing_enable()
model.to(device)

def format_sample(s):
    return f"### Instruction:\n{s['instruction']}\n\n### Response:\n{s['response']}"

texts = [format_sample(s) for s in samples]
ds = Dataset.from_dict({"text": texts})

training_args = SFTConfig(
    output_dir=str(CKPT),
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=2,
    learning_rate=2e-4,
    warmup_steps=10,
    logging_steps=10,
    save_strategy="epoch",
    fp16=False,
    bf16=False,
    dataset_text_field="text",
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=ds,
    processing_class=tokenizer,
)

print("  Resuming training...", flush=True)
trainer.train(resume_from_checkpoint=str(RESUME))

# Save final
model.save_pretrained(str(CKPT))
tokenizer.save_pretrained(str(CKPT))
meta = {"base_model": MODEL_ID, "method": "LoRA (r=16, alpha=32)",
        "device": device, "epochs": 3, "samples": len(samples),
        "checkpoint": str(CKPT), "resumed_from": str(RESUME)}
(TRAIN / "metadata.json").write_text(json.dumps(meta, indent=2))
print("=== Training complete! ===", flush=True)
print(json.dumps(meta, indent=2), flush=True)
