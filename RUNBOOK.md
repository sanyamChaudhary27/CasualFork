# Operating Runbook

## Daily startup

```bash
git status --short
python scripts/verify_company.py --live
opencode
```

Select the desired current model in the OpenCode model picker. For this project the default strategy is to select the strongest effectively-unlimited model for the orchestrator and let subagents inherit it.

## First commands

```text
/company-check
/research-preflight
/red-team current-project-thesis
/gate G0
```

## How to use the company

For normal work, talk to `orchestrator`.

Good request:

```text
Before changing code, determine whether EVOKE or Yume is the safer G1 backend. Delegate independent backend and GPU audits in background, have the novelty reviewer challenge the result, then give me one decision with evidence. Do not edit yet.
```

For a narrow specialist, invoke it directly if needed:

```text
@world-model-researcher audit the official EVOKE i2v inference path and list exact blockers for Colab.
```

## Child-session navigation

Current V2 defaults:

- Down: child-session picker / first child
- Right: next child
- Left: previous child
- Up: parent

The session sidebar/list is the fallback if you changed keybindings.

## Context discipline

- Start new child sessions for independent reviews instead of repeatedly compacting one giant argument.
- The parent receives conclusions; it should not ingest entire upstream repos unless necessary.
- Put durable facts in project files (`RESEARCH.md`, `CLAIMS.md`, experiment manifests), not only conversation context.
- Do not add session-warming hacks unless provider caching is measured to help; fresh independent sessions are a feature for this workflow.

## Git worktrees for parallel builders

Only use when two agents must edit simultaneously:

```bash
git worktree add ../cf-experiment -b agent/experiment
git worktree add ../cf-demo -b agent/demo
```

Each builder gets one worktree. Review and merge centrally. Never have parallel agents mutate the same notebook in the same worktree.

## When to invoke the Server/SDK phase

Write a new decision entry first. Then verify current OpenCode docs and OpenAPI spec before coding against endpoints.

The likely architecture would be a small local controller that talks to one fixed-port `opencode serve`, creates child sessions with `parentID`, uses `prompt_async`, polls `/session/status`, collects messages/diffs, and exposes a queue/dashboard. Do not make the OpenCode agent itself recursively start random additional OpenCode servers.

## Paid GPU rule

Before any paid run, the orchestrator must show:

```text
Experiment ID
Hypothesis
Why Colab/local is insufficient
Exact backend/revision
Exact command/cell
Expected VRAM/runtime
Stop condition
Artifacts to save
Fallback if it fails
```

No exception for "just trying something quickly."
