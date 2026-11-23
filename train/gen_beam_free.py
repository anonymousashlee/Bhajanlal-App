"""Generate data_beam_free.jsonl: Q&A pairs teaching Bhajanlal the Beam Free skill stack."""
import json
from pathlib import Path

TRAIN = Path(__file__).resolve().parent
OUT = TRAIN / "data_beam_free.jsonl"

pairs = [
 ("What skill helps navigate a large codebase without reading every file?",
  "Use git-nexus-knowledge-graph: it builds a pre-computed call-chain and dependency graph so you can query callers, callees, and clusters instead of dumping files."),
 ("How do I keep memory across OpenCode sessions?",
  "Use claude-mem-persistent-memory: it records and compresses agent actions into .opencode/memory/sessions.jsonl and injects only relevant prior context."),
 ("My context window is overflowing with logs. What helps?",
  "Use caveman-token-optimizer: it compresses logs, JSON, and test output while preserving stack traces and error lines."),
 ("What workflow prevents jumping into broken code?",
  "Use everything-claude-code-opencode-port: enforce plan -> test -> implement -> review -> verify, with slash commands /plan /tdd /code-review /verify."),
 ("How do I make UI not look like generic AI output?",
  "Use awesome-md-design-md-token-extractor for design tokens (Linear, Stripe, Vercel palettes, type scales, spacing) and ui-skills-root (improve-ui, frontend-design, improve-animations)."),
 ("Which skills replicate Beam Free deep reasoning?",
  "Combine everything-claude-code-opencode-port (pipeline), get-shit-done (TDD-first terse execution), and tusharkrbarman-skills-for-open-code (sub-agent roles plus /orchestrate)."),
 ("How do I raise reasoning effort in OpenCode?",
  "Use the /variance command to push compatible models to higher reasoning effort; verify active skills with /skills."),
 ("What is the difference between Git Nexus and Graphify?",
  "Git Nexus is symbol-level (callers and callees); Graphify is module and architecture-level (clusters, layers, data flow). Use both for repo-scale navigation."),
]

rows = [{"instruction": q, "response": a} for q, a in pairs]
OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
print("wrote %d samples to %s" % (len(rows), OUT))
