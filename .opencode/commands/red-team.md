---
description: Run independent correctness and novelty attacks on the current claim, plan, experiment, or diff.
agent: orchestrator
---
Red-team this target: $ARGUMENTS

Launch `reviewer` and `novelty-red-team` in background with the same target but do not let them see each other's conclusions initially. If the target involves world-model implementation details, also launch `world-model-researcher`.

Synthesize: strongest correctness objection, strongest novelty objection, which objection is evidence-backed, what experiment would falsify each, and whether work should proceed unchanged, be narrowed, or stop.

Do not edit files unless the user explicitly asked for corrections.
