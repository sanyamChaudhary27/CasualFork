# Decision Log

Record decisions, not brainstorming. Every entry must state what evidence would cause reversal.

## D001 — Native OpenCode V2 subagents before custom session orchestration

**Decision:** Use the built-in `subagent` mechanism and fresh child sessions as the company runtime. Do not build a custom Server/SDK session-spawner yet.

**Why:** Native V2 already supports background child sessions and parent/child lineage. A second control plane adds authentication, port discovery, retries, and API-version surface before a need is demonstrated.

**Reverse if:** we require durable external job queues, arbitrary session forking by message ID, a dashboard, custom retry/scheduling, or native fan-in cannot support the workflow.

## D002 — Model-agnostic company configuration

**Decision:** Do not hard-code Ox Alpha/Kimi model IDs in version-controlled agent files. Let subagents inherit the currently selected parent model.

**Why:** OpenCode's model catalog/variants change; the official guidance is to select available catalog entries rather than guess IDs.

**Reverse if:** we establish stable exact provider/model IDs and measurable benefit from per-role models.

## D003 — Notebook-first until branch quality gate

**Decision:** No significant frontend work before G6.

**Why:** Product polish cannot rescue a world-model branch that does not preserve geometry or obey the intervention.

**Reverse if:** a tiny visualization is necessary to evaluate the experiment itself.

## D004 — Use pretrained world models as environment/backbone

**Decision:** Do not pretrain the foundation world generator from scratch.

**Why:** 48-hour scope and compute economics. Our novelty lives in controlled branching, evaluation, search/controller learning, and presentation.

**Reverse if:** project timeline/compute changes substantially.

## D005 — Search before RL

**Decision:** Best-of-N/CEM/evolution is the first optimizer. RL/controller training is gated behind reward validation.

**Why:** Search provides a fast test of whether our reward ranks genuinely better counterfactuals. RL on a bad reward only scales reward hacking.

**Reverse if:** an existing released RL recipe maps directly to the chosen backend and can be reproduced cheaper than search.

## D006 — Backend choice remains provisional

**Decision:** Start validation with the lowest-risk open candidate that fits available Colab hardware; keep EVOKE as a high-upside research target, not an assumption.

**Why:** released capabilities, memory, dependency stacks, and i2v conditioning caveats differ materially.

**Reverse if:** preflight research/reproduction shows a clearly superior backend.

## D007 — Thesis re-scoped to SC1/SC2 after sealed prior-art adjudication (2026-08-24)

**Decision:** CausalFork's research contribution is narrowed to exactly two falsifiable targets: **SC1** — first *executed* demonstration of prefix/noise-coupled twin branches inside a released pretrained interactive video world model under a deliberate mid-rollout intervention with per-sample locality vs coupling-off controls — and **SC2** — a quantified negative-control result showing uncoupled/naive forks diverge materially more than coupled branches. Formalism claims are abandoned to Twin Rollouts (arXiv:2608.08982); benchmark/dataset novelty claims are abandoned (2608.11601, 2605.27589, 2607.26452, 2604.20460); intervention-capability claims are abandoned (EVOKE MODE=segment; Genie 3). No paid GPU inference before GF0 (strict fork feasibility) adjudication. Search/controller/RL work is POST-SC1 stretch only. Public wording may not use "first" until SC1 verifies AND the novelty audit is refreshed.

**Evidence:** sealed panel 5/6 + adjudication in `fanin/2026-08-24-novelty/`; canonical update commit (RESEARCH/CLAIMS/SPEC/SOURCES/EXPERIMENTS) countersigned by independent reviewer after one REJECT round fixed pointer/wording defects.

**Reverse if:** Twin Rollouts v2 (or any shipped fork-with-shared-noise implementation on an open interactive video WM) publishes executed experiments before us; or GF0 returns INFEASIBLE on every credible backend and the fallback demo cannot honestly carry the thesis.

## D008 — Withhold GPU-01 authorization after final micro-round F10 binding review (2026-08-26)

**Decision:** Do not countersign or execute GPU-01. The final micro-round's two sealed reviewers both returned `PATCH_INCOMPLETE`; the proposal remains NOT EXECUTED.

**Why:** `harness/strict_coupling.py:398-407` validates F10 meta evidence only across branches, while `:572-603` compares digest artifacts only to each other. It never requires each digest F10 hash to equal its corresponding `cpu_rng_sha256_at_fork`; equal null/rehashed digest F10 values plus synthetic equal meta can falsely certify `STRICT_NOISE_COUPLED`.

**Evidence:** `fanin/2026-08-25-semantics/final-micro-round-review-record.md`; sealed M `ses_fc17fc901ffeoe1YiwtRx33NH8` and G `ses_fc17fc815ffeJ7x34dt22DaV48`; direct code inspection above.

**Reverse if:** a CPU fix binds non-null digest F10 to each ledger's at-fork F10 meta, regression-tests the equal-null-digest attack, closes the reviewer-recorded parser/F12/F08/launcher issues as applicable, and a fresh sealed dual delta review returns `PATCH_READY_GPU01_READY`.

## D009 — Continue withholding GPU-01 after validator/guard review (2026-08-26)

**Decision:** Do not countersign or execute GPU-01 after the F10/F12/parser/F08 correction. The proposal remains `PATCH_INCOMPLETE` / NOT EXECUTED.

**Why:** two fresh sealed reviewers independently confirmed that `harness/gpu01_prelaunch.py` is bypassable as a standalone CLI and that it does not attest a computed resolved configuration to `EVOKE_STRICT_CONFIG_SHA256` and the archived pair manifest. These are concrete, CPU-resolvable launch-policy defects, not hypothetical polish.

**Evidence:** `fanin/2026-08-25-semantics/final-validator-launch-guard-review-record.md`; M `ses_fc15e1004ffe4q6DX3kwDkbJtg`; G `ses_fc15dff71ffeIxhGF6Tr0jkmhS`; current primary code cited there.

**Reverse if:** one small mandatory launch wrapper archive-binds a passing prelaunch artifact and canonical resolved config identity, negative tests prove guard-bypass/stale-config rejection, and a fresh sealed two-reviewer delta review returns `PATCH_READY_GPU01_READY`.
