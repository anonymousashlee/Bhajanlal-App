# Bhajanlal - Build vs Fine-Tune Decision

**Decision: fine-tune open-weights base + distill a Flash variant.**

Rationale (revisit when assumptions change):
- No pretraining cluster on this host; full pretrain is out of scope locally.
- Data and evals are the binding constraint, which favors post-training.
- MoE serving economics are preserved by inheriting the base architecture.

Reversal triggers: dedicated pretraining budget, or a capability gap no open
base covers.

Generated automatically by the Bhajanlal orchestrator.
