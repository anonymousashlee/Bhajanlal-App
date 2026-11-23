#!/usr/bin/env python3
"""Bhajanlal v4: fresh LoRA fine-tune on MPS (no optimizer-resume, avoids the
state-dict mismatch that broke resume_v3). Trains from the base model on the
full synthetic coding corpus and saves to checkpoints/bhajanlal-v4."""
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "train"
CKPT = TRAIN / "checkpoints" / "bhajanlal-v4"
DATA = TRAIN / "data_max.jsonl"
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
CACHE = Path.home() / ".cache" / "huggingface"

EPOCHS = 4
BATCH = 1
GRAD_ACCUM = 4
LR = 2e-4


def main() -> None:
    TRAIN.mkdir(parents=True, exist_ok=True)
    print(f"=== Bhajanlal v4 training -> {CKPT.name} ===", flush=True)

    samples = [json.loads(l) for l in DATA.read_text().splitlines() if l.strip()]
    print(f"Loaded {len(samples)} samples from {DATA.name}", flush=True)

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

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, cache_dir=str(CACHE), torch_dtype=torch.float16
    )
    model.gradient_checkpointing_enable()
    model.to(device)

    lora = LoraConfig(r=16, lora_alpha=32, target_modules=["q_proj", "v_proj"],
                      lora_dropout=0.05, bias="none", task_type="CAUSAL_LM")
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    def fmt(s):
        return f"### Instruction:\n{s['instruction']}\n\n### Response:\n{s['response']}"

    ds = Dataset.from_dict({"text": [fmt(s) for s in samples]})

    args = SFTConfig(
        output_dir=str(CKPT),
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LR,
        warmup_steps=10,
        logging_steps=10,
        save_strategy="epoch",
        fp16=False, bf16=False,
        dataset_text_field="text",
        report_to="none",
    )
    trainer = SFTTrainer(model=model, args=args, train_dataset=ds,
                         processing_class=tokenizer)

    print("Training...", flush=True)
    t0 = time.time()
    trainer.train()
    dur = time.time() - t0

    model.save_pretrained(str(CKPT))
    tokenizer.save_pretrained(str(CKPT))

    # final train loss from trainer state
    tr = trainer.state.log_history[-1] if trainer.state.log_history else {}
    meta = {
        "base_model": MODEL_ID, "method": "LoRA (r=16, alpha=32)", "device": device,
        "epochs": EPOCHS, "samples": len(samples), "checkpoint": str(CKPT),
        "train_seconds": round(dur, 1), "final": tr,
    }
    (TRAIN / "metadata_v4.json").write_text(json.dumps(meta, indent=2))
    print(f"=== v4 training complete in {dur/60:.1f} min ===", flush=True)
    print(json.dumps(meta, indent=2), flush=True)


if __name__ == "__main__":
    main()
