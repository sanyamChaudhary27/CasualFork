---
name: evidence-gate
description: Use when deciding whether an experiment gate (G1-G6) passed or failed - checks predeclared success criteria from EXPERIMENTS.md, required artifacts, comparable baselines, reproducibility records, and unsupported inference before issuing PASS/FAIL/CONDITIONAL.
---
# Evidence Gate

For gate `Gx`:

1. Quote its exact success criterion from `EXPERIMENTS.md`.
2. List required artifacts/measurements.
3. Mark each as present, missing, or invalid.
4. Check that the run used the intended backend/version/config.
5. Check for comparison leakage or changed variables.
6. Decide PASS / FAIL / CONDITIONAL.
7. If fail, prescribe the smallest next experiment; do not broaden scope.

A screenshot or anecdote does not satisfy a metric/artifact requirement. Never advance the project stage on a CONDITIONAL or FAIL verdict.
