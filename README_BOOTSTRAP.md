# CausalFork × OpenCode Company Bootstrap

**Target:** current OpenCode V2 behavior as checked on 2026-08-24.

This kit turns one OpenCode project into a small research/engineering organization using **native child-session subagents** first. It deliberately does **not** add a custom HTTP session-spawner on day one. Native V2 already supports fresh child sessions, background subagents, per-agent permissions, and parent/child session navigation. We only escalate to the Server/SDK if native orchestration becomes a measured bottleneck.

## 0. Before copying anything

If this is an existing repository, commit or back up your current `AGENTS.md`, `opencode.json(c)`, and `.opencode/` directory before merging this kit.

## 1. Upgrade OpenCode first

This kit uses current opencode config names: top-level `permission` object, per-agent `permission:` frontmatter maps, and tools named `bash`/`task`. The shapes were validated against <https://opencode.ai/config.json> on 2026-08-24.

```bash
opencode --version
opencode upgrade
opencode --version
```

If `opencode upgrade` is unavailable because your installation is very old, reinstall using the same channel you normally use. Common current options:

```bash
# official install script
curl -fsSL https://opencode.ai/install | bash

# npm
npm install -g opencode-ai@latest

# Homebrew tap (macOS/Linux)
brew upgrade anomalyco/tap/opencode
```

On Windows, OpenCode's current docs recommend WSL for best compatibility. Native npm/Chocolatey/Scoop are alternatives.

Do **not** pin a model ID from this kit. OpenCode's model catalog changes. Select **Ox Alpha Free** (or another model you want) in the TUI. All company subagents intentionally omit a model override, so they inherit the parent model.

## 2. Put this kit at the repository root

Expected structure:

```text
AGENTS.md
COMPANY.md
RESEARCH.md
SPEC.md
EXPERIMENTS.md
CLAIMS.md
DECISIONS.md
RUNBOOK.md
opencode.json
.opencode/
  agents/
  commands/
  skills/
scripts/
```

## 3. Static doctor

Run:

```bash
python scripts/verify_company.py
```

Expected final line:

```text
COMPANY_STATIC_OK
```

Then, with OpenCode installed:

```bash
python scripts/verify_company.py --live
```

This additionally runs `opencode --version` and `opencode agent list` and checks that the company agents are discovered.

## 4. Start OpenCode

From the repository root:

```bash
opencode
```

If web search is unavailable under your selected provider, relaunch with Exa enabled:

```bash
OPENCODE_ENABLE_EXA=1 opencode
```

PowerShell equivalent:

```powershell
$env:OPENCODE_ENABLE_EXA="1"; opencode
```

Select **Ox Alpha Free** in the model picker. We keep model selection outside version-controlled config so the repo never breaks when model IDs/variants change.

## 5. Prove the company can create/manage child threads

Inside OpenCode run:

```text
/company-check
```

The `orchestrator` must dispatch at least three **background subagents**. The test passes only if the parent receives independent outputs from `research-lead`, `reviewer`, and `novelty-red-team`, then synthesizes them without modifying project files.

Current V2 child-session navigation defaults are parent/child oriented: Down opens child selection, Right/Left cycles children, Up returns to parent. Your own keybindings may override these.

## 6. First real command

After `/company-check` passes:

```text
/research-preflight
```

That command asks the orchestrator to commission independent research on model feasibility, causal metrics, novelty, and evidence quality before any notebook is built.

## 7. What not to do yet

- Do not build a custom session API tool until native subagents fail a concrete requirement.
- Do not add session-warming hacks. Fresh child sessions with independent context are strategically better for reviewers and cost nothing extra here.
- Do not give every agent unrestricted shell/edit permission.
- Do not let multiple builders edit the same notebook simultaneously.
- Do not spend paid GPU time before the Colab validation gates say we need it.
- Do not start the frontend before the counterfactual branch experiment works.

## 8. Escalation path: native → Server/SDK

If we later need a dashboard, explicit queue, fan-out/fan-in across arbitrary sessions, persistent job metadata, or programmatic session forking, OpenCode exposes:

- `POST /session` with `parentID?`
- `GET /session/:id/children`
- `POST /session/:id/fork`
- `POST /session/:id/prompt_async`
- `GET /session/status`
- a type-safe `@opencode-ai/sdk`

That is Phase 2. We will build it only after native orchestration is verified and its limitations are written into `DECISIONS.md`.
