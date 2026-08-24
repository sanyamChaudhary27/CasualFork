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
