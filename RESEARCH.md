# CausalFork Research Map

**Frozen snapshot:** 2026-08-24. Re-verify before public release because this area moves quickly.

## Thesis

The project is not "image → explorable world." That capability is already represented by commercial and open systems. The research target is **controlled counterfactual branching**: from the same generated past, apply a semantic/mechanism intervention and produce an alternate future that obeys the intervention while minimizing unrelated change.

## Novelty boundary

### Already established nearby

- **Interactive image-conditioned world generation:** Yume creates dynamic interactive worlds from images and keyboard actions.
- **Persistent external world state + mid-rollout re-prompting:** EVOKE maintains a camera-indexed world-state bank and supports changing prompts during generation.
- **Counterfactual branching formalism for action interventions:** *Twin Rollouts* formalizes factual/counterfactual branches with shared prefix and future exogenous noise, plus locality metrics and simulator counterfactual re-renders; the note states experiments are forthcoming.
- **Structured intervention datasets:** CG-World explicitly records action, observation, mechanism, and strict counterfactual branch lineage in computer-graphics data.
- **RL with verifiable rewards for world models:** RLVR-World demonstrates decoded-output rewards for post-training across language/video world-model settings; PersistWorld applies RL post-training to stabilize autoregressive robot video-world-model rollouts.

### Our intended contribution

A working system for **semantic/mechanism counterfactual interventions** over an interactive video world model, with:

1. branch lineage and reproducibility;
2. shared prefix / camera track / noise policy where controllable;
3. explicit invariant-vs-intervention evaluation;
4. synthetic simulator ground truth for locality tests;
5. best-of-N / CEM or evolutionary search over branch-control parameters;
6. optional learned controller/RL only after the reward is validated;
7. an interactive, viral-quality visualization of alternate realities.

We must not claim invention of counterfactual world-model branching itself.

## Primary references

### Twin Rollouts

- Paper: https://arxiv.org/abs/2608.08982
- Date: 2026-08-10
- Relevant idea: generated factual prefix + coupled future noise + action intervention; minimal-change locality; simulator-ground-truth counterfactual rerenders.
- Important caveat: the paper abstract/note says experiments are forthcoming. Do not imply released empirical results without checking again.

### CG-World

- Paper: https://arxiv.org/abs/2607.26452
- Date: 2026-07-29
- Relevant idea: world-state dataset with explicit branch metadata, invariants, action/observation/mechanism interventions, strict counterfactuals.
- Scale reported in abstract: ~850k temporally aligned 1–5 s segments.

### EVOKE

- Paper: https://arxiv.org/abs/2608.13546
- Code: https://github.com/AlayaLab/Evoke
- Model: https://huggingface.co/AlayaLab/Evoke
- Relevant idea: 14B autoregressive world model with external camera-indexed world state; chunk-level re-prompting; i2v/v2v/t2v modes.
- Reported inference: 1.5 s at 384×640 in 2.11 s on one H200 for the 3-step distilled path.
- Critical caveat: released distilled models were trained on v2v conditioning; distilled i2v/t2v are reported as zero-shot. The stage-1 camera-control model is the released path with all conditioning modes in-distribution.
- Environment caveat: the official repo pins specific CUDA/PyTorch/dependency behavior and requires a separate depth backend. Treat installation as a real engineering risk.
- License caveat: repo is Apache-2.0, but required/optional depth components can have more restrictive licenses. Audit exact chosen backend before commercialization.

### Yume / Yume-1.5

- Paper: https://arxiv.org/abs/2507.17744
- Code: https://github.com/stdstu12/YUME
- Project: https://stdstu12.github.io/YUME-Project/
- Relevant idea: image-conditioned interactive world generation with quantized camera controls and autoregressive memory.
- Current repo news states Yume-5B and Yume-1.5 were released in Dec 2025.
- Why we care: lower-risk first validation candidate before heavier research backends.

### RLVR-World

- Paper: https://arxiv.org/abs/2505.13934
- Relevant idea: post-train world models against verifiable decoded-output metrics rather than only likelihood.
- Use for us: methodological justification for reward-driven post-training, not proof that our proposed reward will work.

### PersistWorld

- Code: https://github.com/Jai2500/PersistWorld
- Paper identifier reported by model resources: arXiv:2603.25685
- Relevant idea: RL post-training on autoregressive self-rollouts to reduce exposure-bias degradation in robot video world models.
- Use for us: evidence that rollout-level RL can matter; not our starting algorithm.

## Competitive landscape warning

A project whose headline is only "walk into one photo" is insufficiently differentiated. For example, Image2World already presents a single-image-to-navigable-world product surface, and World Labs Marble provides generative world creation commercially. Our public story must remain focused on **controlled branching/minimal change**, not generic reconstruction or navigation.

## Backend shortlist

| Backend | Role | Strength | Risk / unknown to verify |
|---|---|---|---|
| Yume-5B | first validation | open, image-conditioned, camera-control lineage | exact Colab memory/runtime on our runtime |
| EVOKE | target research backend | persistent world state + re-prompting | heavy 14B path; i2v distilled path zero-shot; environment complexity |
| AlayaWorld | fallback/research comparison | world-state ideas and prompt control | dependency/memory/licensing complexity |
| Other open interactive WMs | contingency | may be easier/faster | must prove released code/weights and branch-compatible conditioning |

Do not lock the final backend until the same small branch protocol is run on at least two credible candidates or one candidate decisively clears the gates.

## Research questions that must be answered before product build

1. Can we preserve an exactly identical prefix by reusing generated latents/video/state rather than regenerating it?
2. Can the backend expose or deterministically reconstruct future exogenous noise so a counterfactual branch can be noise-coupled?
3. What backend state must be cloned at the fork: latent history, point cloud/world bank, prompt schedule, random generator, camera pose, cache?
4. Does changing the prompt at a chunk boundary preserve geometry enough to be meaningful?
5. Which intervention classes are realistically controllable in 48 hours: lighting/weather/material/global event/object presence/layout?
6. Which metrics correlate with human judgment of "same world, one changed fact"?
7. Can synthetic Blender branch pairs provide ground-truth invariant/change masks cheaply enough?
8. Does best-of-N/CEM materially improve branch quality over a fixed generation recipe?
9. If a controller is trained, can it generalize to held-out scenes/intervention classes rather than memorize prompt recipes?
10. What is the smallest demo that remains honest if strict noise coupling or state cloning is unavailable in the chosen backend?

## Research completion criteria

`RESEARCH.md` is not "done" when it is long. It is ready when each material implementation decision points to an official source or reproduced experiment, every license is understood, and the novelty-red-team cannot identify an obvious prior system that already implements our full claim.
