#!/usr/bin/env python3
"""Self-check for the post-training validation gate (no GPU / no model load).

Feeds the real metric sets from metadata_v4.json (healthy) and
metadata_v5.json (broken) through validate_run with a stub model, and asserts
the gate rejects the broken run and accepts the healthy one. Also asserts the
silent alpaca fallback in fmt() is really gone.
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("tv5", HERE / "train_v5.py")
tv5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tv5)


class StubEnc(dict):
    """Mimics a BatchEncoding well enough for the smoke test."""
    def to(self, device):
        return self


class _Ids(list):
    @property
    def shape(self):
        return (1, len(self))


class StubTok:
    """Pretends the chat template rendered fine and decoding gives text."""
    eos_token_id = 0

    def apply_chat_template(self, msgs, tokenize=False, add_generation_prompt=False):
        return "<|im_start|>user\nhi\n<|im_start|>assistant\n"

    def __call__(self, prompt, return_tensors=None, **kw):
        return StubEnc({"input_ids": _Ids([1, 2, 3])})

    def decode(self, ids, skip_special_tokens=True):
        return "OK"


class StubModel:
    def generate(self, **kw):
        return [[1, 2, 3, 4]]


def final_of(name):
    d = json.loads((HERE / name).read_text())
    return d.get("final", {})


failures = []


def check(label, cond, detail=""):
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {label}{(' -> ' + detail) if detail else ''}")
    if not cond:
        failures.append(label)


print("1. broken v5 metrics must be REJECTED")
v5 = final_of("metadata_v5.json")
probs = tv5.validate_run(v5, StubModel(), StubTok(), "cpu")
for p in probs:
    print(f"       caught: {p}")
check("v5 rejected", len(probs) >= 2, f"{len(probs)} problem(s)")
check("v5 accuracy gate fired",
      any("mean_token_accuracy" in p for p in probs))
check("v5 entropy gate fired", any("entropy" in p for p in probs))

print("\n2. healthy v4 metrics must be ACCEPTED")
v4 = final_of("metadata_v4.json")
probs4 = tv5.validate_run(v4, StubModel(), StubTok(), "cpu")
check("v4 accepted", probs4 == [], "; ".join(probs4) or "no problems")

print("\n3. NaN / missing / absurd values must all be rejected")
for label, blob in [
    ("entropy NaN", {"train_loss": 0.4, "entropy": float("nan"),
                     "mean_token_accuracy": 0.9}),
    ("loss inf", {"train_loss": float("inf"), "entropy": 0.4,
                  "mean_token_accuracy": 0.9}),
    ("accuracy missing", {"train_loss": 0.4, "entropy": 0.4}),
    ("accuracy 0.0", {"train_loss": 0.38, "entropy": float("nan"),
                      "mean_token_accuracy": 0.0}),
]:
    p = tv5.validate_run(blob, StubModel(), StubTok(), "cpu")
    check(label + " rejected", len(p) >= 1, "; ".join(p))

print("\n4. smoke-test failures must be rejected")
p = tv5.validate_run(v4, StubModel(), type("T", (), {
    "eos_token_id": 0,
    "apply_chat_template": lambda self, *a, **k: "",
})(), "cpu")
check("empty render rejected", any("empty smoke prompt" in x for x in p),
      "; ".join(p))


print("\n5. silent alpaca fallback must be gone from fmt()")
src = (HERE / "train_v5.py").read_text()
check("no '### Instruction' fallback", "### Instruction:" not in src)
check("fmt raises instead of falling back",
      "Refusing to train on a fallback format" in src)

print("\n6. gate must block promotion in main()")
check("failed path quarantines", "def quarantine" in src and
      "REJECTED.txt" in src)
check("failed path writes status=failed", '"status": "failed"' in src)
check("failed path exits non-zero", "sys.exit(1)" in src)
check("validate runs before save_pretrained",
      src.index("validate_run(tr") < src.index("model.save_pretrained"))

print("\n" + ("ALL CHECKS PASSED" if not failures
             else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
