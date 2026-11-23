# Bhajanlal - Beam Free Skill Stack

Replicates Reflection's Beam Free capabilities using a curated stack of OpenCode skills.

## Context and Codebase Navigation (replicates 1M window)
- git-nexus-knowledge-graph - pre-computed call-chain and dependency graph
- graphify - module and architecture graph
- claude-mem-persistent-memory - cross-session compressed memory
- caveman-token-optimizer - compress logs, JSON, test output

## Reasoning and Execution Workflows (replicates planning)
- everything-claude-code-opencode-port - plan -> test -> implement -> review -> verify
- get-shit-done - terse, TDD-first, vertical slices
- tusharkrbarman-skills-for-open-code - sub-agent roles plus /plan and /orchestrate
- ibelick-ui-skills - frontend polish rules

## UI and Frontend Generation (clean interfaces)
- awesome-md-design-md-token-extractor - design tokens (Linear, Stripe, Vercel)
- ui-ux-pro-max - design systems, palettes, typography
- ui-skills-root - improve-ui, frontend-design, improve-animations

## Activation
1. Skill folders live in ~/.config/opencode/skills/<id>/SKILL.md.
2. Rebuild library: cd ~/.config/opencode/skill_build && python3 build.py.
3. In OpenCode: /skills to view and toggle; /variance to raise reasoning effort.
4. Orchestrator library phase re-verifies coverage (800/800 target).

## Training data
- train/gen_beam_free.py generates train/data_beam_free.jsonl with Q&A pairs
  covering these skills so the model learns to invoke them.
