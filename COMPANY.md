# OpenCode Company

## Why this exists

The company is a coordination pattern over **native OpenCode V2 child sessions**, not a fictional multi-agent framework. A primary orchestrator delegates bounded tasks to fresh-context subagents, optionally in the background, then integrates evidence.

The design goal is **independent reasoning with controlled write access**.

## Organization

```text
                         orchestrator
                              │
       ┌───────────────┬──────┼───────┬────────────────┐
       │               │      │       │                │
 research-lead   world-model  causal  gpu-engineer   reviewer
       │          researcher metrics      │             │
       │               │      │       experimenter   novelty-red-team
       │               │      │             │
       └────────────── evidence ─────── demo-director
```

## Roles

### orchestrator — decision owner

Owns sequencing, delegation, integration, gate decisions, and project documents. It should not personally redo all specialist research. It may edit broadly, but must preserve working baselines and obtain dissent for major decisions.

### research-lead — evidence map

Audits literature, official docs, release state, dates, and claim quality. Read-only.

### world-model-researcher — backend truth

Inspects model repos, inference paths, conditioning modes, VRAM/runtime evidence, checkpoint availability, dependencies, and licenses. Read-only.

### causal-metrics-researcher — evaluation science

Defines what "minimal change" and "same world" mean, prioritizing simulator-ground-truth metrics over learned judges. Read-only.

### data-rl-researcher — data/search/learning strategy

Designs synthetic causal pairs, experience buffers, best-of-N/CEM, and only later learned controllers or RL. Read-only unless explicitly reassigned.

### gpu-engineer — accelerator reliability

Diagnoses CUDA, memory, attention kernels, dtypes, offload, compile paths, and performance. May edit notebooks/scripts in assigned scope; shell remains approval-gated by default.

### experimenter — reproducible builder

Builds notebooks, experiment harnesses, logging, metrics, and backend adapters. This is the main implementation subagent before product work.

### reviewer — correctness gate

Reviews diffs, experiments, tests, claims, and regressions without editing.

### novelty-red-team — "wrapper detector"

Tries to prove the contribution is already done, trivial, misleading, or not causally controlled. Read-only; must produce falsifiable objections rather than vibes.

### demo-director — communication layer

Only becomes important after the core branch effect works. Optimizes the hero interaction/clip while preserving technical honesty.

## Delegation contract

A good delegation is narrow enough that a child can finish with fresh context:

```text
Question: Can EVOKE's released i2v path support our branch protocol on one H100?
Evidence required: official repo/model card + exact inference mode + memory/runtime evidence.
Do not edit files.
Return: conclusion, evidence, uncertainty, recommendation, blockers.
```

A bad delegation is:

```text
Research EVOKE and build the project.
```

## Child result statuses

The orchestrator classifies every child return into exactly one status:

| Status | Meaning |
|---|---|
| SUCCESS | Completed with usable evidence |
| RESEARCH_NEGATIVE | Completed; the genuine answer is negative or empty — this is a real result |
| INFRA_FAILURE | Provider/network/runtime failure; carries zero evidential weight |
| PERMISSION_FAILURE | Blocked by permissions/config; retry after wiring is fixed |
| TIMEOUT | Exceeded bounds; may be retried with reduced scope |
| INVALID_EVIDENCE | Content returned but fails citation/evidence standards |

Infrastructure or provider failure must never be interpreted as research evidence. A failed red-team is not a passed red-team.

## Fan-out / fan-in pattern

For a major decision the orchestrator should:

1. Dispatch 2–4 independent subagents **in background**.
2. Continue only non-conflicting work while they run.
3. Read each child result separately.
4. Identify disagreements, not just majority opinion.
5. If disagreement is material, dispatch a reviewer with both positions.
6. Record the decision and evidence in `DECISIONS.md`.

## Sealed review protocol

For material decisions (novelty, backend choice, reward design, thesis changes), reviews run through the sealed pipeline. Use `FANIN_TEMPLATE.md` as the canonical record format.

- **STAGE 1 — Independent dispatch.** All panelists receive the same research question, evidence requirements, project constraints, and primary-source requirement. They do NOT receive one another's findings.
- **STAGE 2 — Sealed returns.** For each panelist record: session ID, role, dispatch time/order, return status (see Child result statuses), evidence tier, primary sources inspected, verdict, confidence, unresolved questions.
- **STAGE 3 — Reveal.** Only after all usable independent reports are sealed may reports be exposed to a synthesis agent.
- **STAGE 4 — Adversarial synthesis.** Synthesis must preserve disagreements rather than average them.
- **STAGE 5 — Adjudication.** A separate adjudicator checks the synthesis against primary sources before any root research claim is changed.

## Write ownership

Default ownership:

| Area | Writer |
|---|---|
| Root research/spec docs | orchestrator |
| Notebook / experiment code | experimenter |
| CUDA/perf patches | gpu-engineer, only when assigned |
| Product/demo | demo-director or experimenter, after G6 |
| Reviews | nobody; reviewers report only |

If parallel writing is required, isolate with Git worktrees.

## Gate adjudication

Gates follow: experiment owner proposes → reviewer independently verifies evidence → orchestrator adjudicates.

Without independent reviewer approval, a gate is **UNVERIFIED** — never PASS. The orchestrator may not countersign its own experiments.

## GPU experiment proposal gate

No paid-GPU run starts without a completed proposal. Integrated with the `experiment-reproduction` skill: the proposal is the front matter of the same manifest that skill already requires — do not maintain two formats.

Required fields:

- Research question
- Hypothesis
- Decision affected
- Cheapest falsification
- CPU alternative
- Colab alternative
- Requested GPU/VRAM
- Expected paid-GPU consumption
- Success criterion
- Failure criterion
- Artifacts to preserve
- Reviewer countersignature

If the CPU or Colab alternative can answer the question, the paid run is rejected.

## Thread/session management

Native V2 subagents already create child sessions with fresh context. That is our first implementation of "other threads in the same project." The orchestrator should prefer this to manually opening unrelated top-level sessions because parent/child lineage is preserved.

Escalate to OpenCode's Server/SDK only if we need one of these:

- arbitrary session queueing independent of a parent turn;
- persistent job metadata/dashboard;
- explicit programmatic `fork` at message IDs;
- custom scheduling/retry policy;
- cross-session result harvesting beyond native subagent UX;
- integration with an external control plane.

Until one of those is real, custom orchestration code is unnecessary surface area.

## Company health test

Run `/company-check`.

Pass criteria:

- orchestrator is active;
- at least three named subagents are launched;
- they appear as child sessions;
- outputs are independent and role-appropriate;
- parent synthesizes without pretending children said the same thing;
- no files are changed.
