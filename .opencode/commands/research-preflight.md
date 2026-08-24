---
description: Commission the research company to re-audit backend feasibility, novelty, metrics, and data/learning plan before implementation.
agent: orchestrator
---
Perform a research preflight for CausalFork before notebook implementation.

Launch in background:

- `research-lead` to re-check the current literature/release landscape and dates;
- `world-model-researcher` to compare the top 2–4 actually released backends for G1–G6;
- `causal-metrics-researcher` to critique the minimal-change evaluation and synthetic ground-truth plan;
- `data-rl-researcher` to critique best-of-N/CEM/controller/RL sequencing;
- `novelty-red-team` to try to invalidate the contribution as already-done or wrapper-level.

Require evidence and explicit uncertainty from each. Then ask `reviewer` to inspect the combined recommendation for unsupported claims.

Only after that review, update `RESEARCH.md`, `CLAIMS.md`, and `DECISIONS.md` where new verified information materially changes them. End with one backend recommendation for the first Colab validation and the exact unresolved questions that G1–G6 must answer.
