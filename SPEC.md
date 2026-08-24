# CausalFork Technical Specification

## 1. Problem statement

Given an input observation/image `x0`, a generated factual prefix up to fork time `t*`, a future camera/control trajectory `A[t*:T]`, and an intervention `I`, generate a counterfactual continuation that:

1. satisfies `I`;
2. preserves the same history before `t*`;
3. follows the same future camera/control trajectory;
4. preserves non-intervened scene identity/geometry as much as possible;
5. minimizes unintended divergence.

The user-facing product is **RealityFork**. The research system is **CausalFork**.

## 2. Formal view

Let the world generator be:

`Y = G(x0, A, P, ε, S)`

where:

- `A` = camera/action sequence;
- `P` = prompt / condition schedule;
- `ε` = stochastic generation noise;
- `S` = persistent model/world state when exposed by the backend.

At fork time `t*` create:

- factual branch `F`;
- intervention branch `C`.

Desired coupling:

- `prefix_F[0:t*] == prefix_C[0:t*]` exactly at the stored artifact/state level where possible;
- `A_F[t*:T] == A_C[t*:T]`;
- `ε_F[t*:T] == ε_C[t*:T]` when the backend exposes deterministic/coupled noise control;
- `P_C` differs only through intervention `I` and any derived control schedule.

When exact noise/state coupling is impossible, the system must label the comparison as **prefix-shared / seed-matched** rather than strict counterfactual coupling.

## 3. Minimal-change objective

For a generated counterfactual candidate `C`, define a reward vector rather than hiding everything in one scalar:

- `R_intervention`: requested change is present;
- `R_identity`: unchanged content retains identity;
- `R_geometry`: structural geometry remains aligned;
- `R_temporal`: branch is temporally coherent;
- `R_camera`: generated motion follows requested camera trajectory;
- `R_locality`: changes are concentrated in causally/semantically relevant regions;
- `R_artifact`: penalty for visible generation failures.

A scalar search reward may be:

`R = ws*R_intervention + wi*R_identity + wg*R_geometry + wt*R_temporal + wc*R_camera + wl*R_locality - wa*R_artifact`

Weights are experimental parameters and must not be tuned only on the hero demo.

## 4. Intervention taxonomy

Rank interventions by feasibility and causal clarity.

### Tier A — global but structure-preserving

- day ↔ night;
- rain / snow / fog;
- abandoned/overgrown aging;
- wet/dry material state;
- lighting color/intensity.

These are ideal first targets because they can visibly diverge while leaving architecture unchanged.

### Tier B — localized semantic state

- door open/closed;
- one object removed/added;
- lamp on/off;
- surface broken/intact.

These give stronger locality tests but are harder for current generative world models to preserve exactly.

### Tier C — mechanism interventions

- gravity direction;
- flooding level dynamics;
- fire spread or growth dynamics;
- physical rule change.

These are "wamuuuu" stretch goals and should not block the core demo.

## 5. Branch state

Every branch record should be serializable as:

```text
branch_id
parent_branch_id
fork_time_or_chunk
root_input_asset
backend_name
backend_revision
factual_prefix_artifact
world_state_checkpoint?        # if backend exposes it
camera_trajectory
base_prompt
intervention_spec
prompt_schedule
seed
noise_policy                   # coupled | reused-seed | uncontrolled
sampling_parameters
metric_vector
output_artifacts
provenance
```

No UI concept should exist without a corresponding data record.

## 6. Backend interface

All world-model experiments should target one small adapter contract:

```text
prepare(input_image, base_prompt, config) -> SessionState
rollout(state, camera_actions, prompt_schedule, rng_policy) -> Rollout
fork(state_or_rollout, fork_point) -> BranchState
continue(branch_state, camera_actions, prompt_schedule, rng_policy) -> Rollout
metrics(factual, counterfactual, intervention, optional_ground_truth) -> MetricVector
```

The first backend may implement `fork` by storing/reusing a rendered prefix if hidden state cloning is unavailable. Later adapters can clone external world state or latent history.

## 7. Search/controller layer — our learning contribution

### Phase A: fixed recipe baseline

Generate one counterfactual continuation with a hand-written intervention schedule.

### Phase B: best-of-N

Sample `N` control parameter sets, score each, retain the best.

### Phase C: CEM/evolutionary search

Search over parameters such as:

- intervention prompt decomposition;
- positive/negative prompt strength;
- intervention onset chunk;
- ramp duration;
- history/world-memory strength if exposed;
- conditioning blend;
- resampling amount;
- seed/noise schedule when permitted.

### Phase D: learned controller

Only after enough `ForkBuffer` data exists, train a small policy/value/ranker that maps scene/intervention embeddings plus previous trial results to promising generation controls.

### Phase E: RL (optional)

Only if Phase C demonstrates a trustworthy reward and Phase D has a meaningful baseline. RL is a stretch goal, not a badge.

## 8. Data

### RealityBench

A small real-image set across indoor/outdoor scene types with standardized intervention prompts and camera paths. Used for qualitative/metric evaluation, not ground-truth causal locality.

### CausalPairs

Synthetic Blender/simulator scenes rendered twice from the identical state/trajectory with exactly one controlled intervention. Store RGB, depth, segmentation/object IDs, camera matrices, intervention metadata, and changed-vs-invariant masks.

### ForkBuffer

All generation attempts plus controls and reward vectors. Used for search analysis and potential controller training.

## 9. Tier-1 MVP contract

One source photo must produce:

1. a short factual exploration;
2. a fork at a deterministic chunk boundary;
3. a counterfactual intervention from Tier A;
4. identical stored prefix;
5. identical future camera track;
6. synchronized branch playback;
7. clearly visible requested divergence;
8. strong preservation of room/building geometry;
9. a metric panel explaining the tradeoff;
10. a reproducibility record.

## 10. Non-goals for the 48-hour build

- pretraining a foundation world model;
- universal physical causality;
- arbitrary object editing with perfect locality;
- production auth/payments/multi-tenant serving;
- guaranteed true real-time generation;
- claiming strict causal identification when backend stochastic state cannot be coupled;
- mobile polish before the hero desktop demo works.

## 11. Public positioning

Use precise language:

> "CausalFork searches for a counterfactual continuation of the same generated world under a controlled semantic/mechanism intervention, while explicitly rewarding preservation of everything that should not change."

Avoid:

> "We built a world model from scratch."

> "It perfectly simulates causality."

> "It is real-time" unless measured.
