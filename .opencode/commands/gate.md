---
description: Evaluate a named experiment gate against its predeclared evidence and decide pass/fail without scope creep.
agent: orchestrator
---
Evaluate gate `$1` using `EXPERIMENTS.md` and the `evidence-gate` skill.

Delegate evidence inspection to `reviewer` and the most relevant specialist. Require exact artifact/measurement references. Return PASS, FAIL, or CONDITIONAL with missing evidence and the single smallest next experiment.

Do not advance the project stage on a conditional or failed gate.
