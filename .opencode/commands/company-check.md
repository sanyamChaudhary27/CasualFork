---
description: Verify native OpenCode child-session orchestration with independent background specialists.
agent: orchestrator
---
Run a non-destructive company health check. Do not edit any file.

Use the native subagent tool to launch these three child sessions **in background**:

1. `research-lead`: inspect only the project constitution and return `COMPANY_OK:RESEARCH` plus one research-risk observation.
2. `reviewer`: inspect only the project constitution/config conceptually and return `COMPANY_OK:REVIEW` plus one invariant the orchestrator must protect.
3. `novelty-red-team`: inspect the stated CausalFork thesis and return `COMPANY_OK:NOVELTY` plus one falsification test for the novelty claim.

After all three return, synthesize a table with child name, token, independent observation, and pass/fail. Confirm that they were child sessions and that no files changed. If any child failed, explain the smallest fix. Do not paper over disagreements.
