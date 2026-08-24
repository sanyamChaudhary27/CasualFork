# Experiment Plan and Gates

## Principle

No stage advances because a model "looks promising." It advances because a predeclared gate passes.

## Compute ladder

### Local CPU

Use for repository setup, parsing, adapter unit tests with mock tensors, metrics on saved frames, prompt/search logic, documentation, and static verification.

### Colab — first hardware gate

Use to prove environment installation, official upstream sample, reduced-resolution custom input, camera controls, branch plumbing, deterministic prefix behavior, and a first intervention. A T4/L4 is not required to prove final fidelity; it is a pipeline validation environment.

### Lightning.ai — premium burst

Use only after the notebook is already reproducible. Spend H100-class time on heavy backends, search batches, and final hero candidates rather than package debugging.

### AWS — engineering reserve

Use when we need a longer-lived GPU machine, larger VRAM, or service-style integration after the experiment path is known. Verify GPU-family quota before depending on it.

## Gate table

| Gate | Question | Required evidence | Fail action |
|---|---|---|---|
| GF0 | STRICT FORK FEASIBILITY — before any paid inference: can the chosen backend expose, snapshot, clone, replay, or otherwise control all state required for meaningful future-noise coupling at the branch point? | code-level trace of RNG creation/use; scheduler/generator behavior; state-bank mutation behavior; branch-state clone strategy; identified tensor/state boundary; proof or falsification of deterministic continuation assumptions. CPU/static-analysis FIRST. **GF0 cannot PASS from documentation alone.** | downgrade to prefix-shared/seed-matched per SPEC §2a fallback rule |
| G0 | Is the environment known? | hardware/software report saved | fix environment only |
| G1 | Does official upstream inference run? | unmodified official sample + artifact | stop custom code |
| G2 | Does our input run? | custom source image produces output | change input/profile/backend |
| G3 | Does camera control visibly work? | fixed camera path + expected motion | inspect control encoding |
| G4 | Can we create an identical stored prefix? | prefix hashes/bytes or documented state clone | downgrade claim or change backend |
| G5 | Can one intervention visibly change the future? | synchronized factual/counterfactual clips (SC1 ablation branches per SPEC §2b) | adjust backend/prompt schedule |
| G6 | Is unrelated structure preserved enough? | metrics + human review above threshold | search/reward/backend work |
| G7 | Does search beat a fixed recipe? **CONDITIONAL on SC1 success** | held-out best-of-N/CEM comparison | do not add RL |
| G8 | Does a learned controller beat search baseline? **CONDITIONAL on SC1+G7 success** | held-out evaluation | keep search-only contribution |
| G9 | Is the hero demo reproducible? | one-command/notebook rerun + artifact manifest | no launch yet |

**No paid inference may start before GF0 is adjudicated.** Frontend work may begin after **G6**. Search/RL gates (G7/G8) are POST-SC1 stretch work per the 2026-08-24 adjudication and SPEC §7.

## GF0 — strict fork feasibility (CPU/static first)

Question: can the chosen backend expose, snapshot, clone, replay, or otherwise control all state required for meaningful future-noise coupling at the branch point?

Required evidence (all code-level, pinned commit):

- RNG call graph: where `torch.Generator` objects are created, `manual_seed` calls, `randn`/`randn_tensor` calls, device-specific RNG state;
- scheduler/generator stochasticity behavior per generation chunk;
- world-state-bank mutation points and eviction behavior;
- branch-state clone strategy (deepcopy sufficiency; tensor aliasing);
- identified tensor/state boundary that must be serialized at fork time;
- proof or falsification of deterministic continuation assumptions.

Rules:

1. CPU/static analysis first; no model-weight download unless a tiny config/tokenizer file is essential.
2. **GF0 cannot PASS from documentation alone** — documentation claims must be confirmed against actual code paths.
3. A mock/model-free fork harness (backend-agnostic) must demonstrate our infrastructure can hold future noise equal across restored branches before any backend claim.
4. Verdict vocabulary: GF0_STRICT_FEASIBLE | GF0_FEASIBLE_WITH_PATCH | GF0_SEED_MATCHED_ONLY | GF0_INFEASIBLE.

## G0 — runtime audit

Capture:

```text
GPU model
VRAM
system RAM
disk free
OS
Python
PyTorch
CUDA runtime
NVIDIA driver
compute capability
bf16 support
flash-attention availability
xformers/SDPA state
```

Do not infer hardware from the Colab plan name.

## G1 — upstream baseline

Rules:

- clone/pin upstream;
- use official model revision;
- run official sample before modifications;
- save exact command and logs;
- do not optimize yet.

Success is binary: an official output exists and is visually sane.

## G2/G3 — custom source and camera track

Use one deliberately easy scene first: a well-lit indoor room with clear planar geometry and limited motion.

Define a fixed short camera track such as:

```text
forward
forward
yaw +20°
forward
yaw -10°
forward
```

The same serialized track is reused by all branches/backends.

## G4 — prefix identity

Preferred order:

1. clone backend state at the fork;
2. reuse stored latent/history/state plus exact RNG state;
3. reuse already-generated prefix frames and branch only future generation;
4. deterministic replay from same seed as last resort.

Record which level is achieved. Do not call level 4 "exact state forking."

## G5/G6 — first counterfactual

Start with a Tier-A intervention:

> "The same room 100 years after humans disappeared; preserve walls, doors, windows, camera geometry and layout."

Generate factual and counterfactual branches under the same future camera track.

### Core metrics

Store metrics separately; never optimize only a weighted scalar.

- semantic intervention score;
- DINO/SigLIP identity similarity on invariant regions;
- depth/geometry consistency;
- feature correspondence / reprojection consistency when available;
- optical-flow/temporal consistency;
- camera-control fidelity;
- locality score: change inside intended region/context vs outside;
- artifact score;
- human paired preference.

For global interventions like weather/aging, locality is semantic rather than a tiny pixel mask. Define invariants explicitly (walls/doors/layout) and allow appearance changes that logically follow the intervention.

## CausalPairs synthetic benchmark

Create a tiny simulator dataset before claiming causal locality.

Each scene should export:

```text
scene_id
factual_state
counterfactual_state
intervention_type
intervention_target
invariant_object_ids
camera_trajectory
RGB factual/counterfactual
depth
segmentation/object IDs
changed-region mask
camera matrices
```

Initial scenes should be simple enough to debug: room, chair, table, lamp, door, window, one light source.

Suggested interventions:

- lamp on/off;
- chair visible/removed;
- door open/closed;
- floor dry/wet;
- lighting day/night.

Avoid fancy physics until the evaluation pipeline is correct.

## G7 — search experiment

Baseline: fixed hand-written generation recipe.

Search: best-of-N then CEM/evolution over a bounded control vector.

Use held-out scenes/interventions. Report:

- average reward vector;
- best-of-N gain;
- wall-clock/GPU cost per accepted branch;
- failure modes;
- whether improvements are merely prompt adherence at the expense of preservation.

Only if search reliably improves human judgments should we claim "the system evolves alternate realities."

## G8 — controller/RL

`ForkBuffer` rows should include:

```text
scene embedding / ID
intervention embedding / spec
backend + revision
control vector
seed/noise policy
metric vector
human label if available
cost/latency
artifact paths
```

First train a ranker/controller with supervised preference or contextual-bandit style learning. Compare against search with equal or clearly reported compute budgets.

RL is allowed only if:

- reward hacking tests pass;
- train/validation interventions are separated;
- the learned policy improves held-out branch quality;
- training cost fits remaining compute.

## Ablations worth doing

1. Same seed vs uncontrolled seed.
2. Shared prefix artifact vs deterministic replay.
3. Prompt switch abruptly vs ramped schedule.
4. Search reward with/without geometry term.
5. Search reward with/without identity term.
6. World-state memory enabled/disabled when backend supports it.
7. Fixed recipe vs best-of-N vs CEM.
8. Synthetic-only reward calibration vs real-image human preference.

## Hero demo selection

Do not cherry-pick invisibly. It is fine to select a hero seed, but report that the hero was selected from `N` candidates and preserve the experiment manifest.

The hero clip should be 8–15 seconds, understandable without narration, and end before model drift becomes the dominant impression.
