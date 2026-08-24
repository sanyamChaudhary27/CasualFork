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
