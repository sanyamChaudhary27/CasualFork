# CausalFork Research Map

**Frozen snapshot:** 2026-08-24 (post sealed-adjudication update, commit history in Git). Re-verify before public release because this area moves quickly.

## Thesis

The project is not "image → explorable world," and it is **not the invention of counterfactual branching**. Interactive world generation already exists commercially and openly, and *Twin Rollouts* (arXiv:2608.08982, v1 2026-08-10) already owns the formalism for noise-coupled factual/counterfactual branches with minimal-change locality evaluation.

The adjudicated research target (sealed prior-art panel + STAGE 5 adjudication, 2026-08-24) is **executed controlled coupling**:

- **SC1 — First *executed* demonstration of prefix/noise-coupled twin branches inside a released pretrained interactive video world model**, under a deliberate mid-rollout intervention, measuring per-sample locality against coupling-off controls.
- **SC2 — Quantified negative-control result**: uncoupled/naive prompt-edit forks produce materially more unintended divergence than properly coupled branches, under a predeclared comparison.

We must not claim invention of counterfactual world-model branching itself. We may only claim execution and measurement of what the field has formalized but not yet demonstrated at scale (as of the 2026-08-24 audit).

## Novelty boundary

### Owned by others (never claim)

- **Counterfactual branching formalism:** *Twin Rollouts* (arXiv:2608.08982) formally defines explicit-noise rollouts, interventions (`do(a_t*:=a')` / `do(x_t*:=x')`), descendant-mask locality metric L, outcome-fidelity O, verifiable reward R=−(λ_O·O+λ_L·L), and simulator-forked ground truth. VERIFIED from v1 full text 2026-08-24. The formalism belongs to them.
- **Mid-rollout semantic-event intervention as a capability claim:** EVOKE's released code implements scheduled per-chunk re-prompting (`MODE=segment`, `schedule_*.json`) during ongoing generation with anchored scene structure; Genie 3 officially ships "promptable world events" (weather changes/object spawning, framed as "what if" scenarios; closed preview). The *capability* is occupied; neither offers branch pairs or locality measurement.
- **Controlled counterfactual benchmarks/datasets:** driving counterfactual prediction (arXiv:2608.11601) builds a CARLA benchmark with ground-truth matched counterfactual outcomes and *has experiments*; What-If World (arXiv:2605.27589) scores 319 single-variable prompt-intervention pairs on real frames with a rubric (APEO), not simulator ground truth; CCTVBench (arXiv:2604.20460) pairs real clips with generated counterfactuals for VideoQA; CG-World (arXiv:2607.26452) records 5,000 strict mechanism + 5,000 strict action counterfactual branches with invariant sets (dataset access gated; noncommercial license).
- **Editing-based counterfactual video generation:** CWMDT (arXiv:2511.17481) conditions video diffusion on LLM-edited digital twins.
- **Prefix-branching RL post-training:** PersistWorld (arXiv:2603.25685; venue UNVERIFIED) trains RL on K=16 continuations branched from a frozen self-generated prefix sharing actions and varying noise — the stated dual of noise-coupled twin rollouts.

### Surviving novelty (falsifiable negative-search result, audit date 2026-08-24)

Three independent sealed searchers, resolving primary sources individually and blind to one another, unanimously found **no executed, open implementation of the complete SC1 combination** — a released pretrained interactive video world model running shared-prefix/noise-coupled twin branches under a deliberate mid-rollout intervention with per-sample locality measured against coupling-off controls.

This is a negative search result as of a specific date. It is **not proof of priority**. Absence of evidence is not evidence of absence. The search must be refreshed immediately before any release or public priority claim, and public wording must not use "first" until SC1 is independently verified AND the novelty audit is re-run clean.

## Primary references

### Twin Rollouts

- Paper: https://arxiv.org/abs/2608.08982
- Identity (VERIFIED 2026-08-24 from abstract + full HTML): "Twin Rollouts: Noise-Coupled Counterfactual Branching in Interactive Video World Models," Ma/Shi/Xu, v1 2026-08-10, no code/data links.
- Status: **owns the formalism** — explicit-noise rollouts, action/state interventions at t*, descendant-mask locality L, simulator-ground-truth outcome fidelity O, verifiable reward R=−(λ_O·O+λ_L·L).
- Experimental status: **v1 contains no full experiments** — abstract: "experiments are forthcoming"; §3 is a deterministic grid-world existence proof; §5: scale-up "deferred to the next revision." Reward is defined, not validated. Viewpoint-moving interventions make L vacuous pending camera-compensated comparison; training signal confined to viewpoint-preserving interventions.
- Consequence for us: any formalism-novelty claim is dead; our claims must anchor on executed measurement (SC1/SC2). Monitor for v2.

### Driving counterfactual prediction

- Paper: https://arxiv.org/abs/2608.11601 ("How Can Driving World Models Do Counterfactual Prediction?", Zhang et al., 2026-08-12)
- VERIFIED 2026-08-24. Formalizes abduction–action–prediction for driving world models; controlled CARLA benchmark with factual + matched counterfactual outcomes and ground truth; shows direct prediction fails; training-free pipeline. Has experiments.
- Consequence: occupies "controlled CF benchmark with ground truth" in the driving domain; closest executed neighbor; cite and differentiate (non-interactive, no noise coupling, no camera-shared twin branches).

### What-If World

- Paper: https://arxiv.org/abs/2605.27589 (Cai et al., 2026-05-26)
- VERIFIED 2026-08-24 by adjudicator. 319 single-variable prompt-intervention pairs on real nuScenes/DROID frames; APEO rubric including Environment ("preserves the shared scene"); best model ~52%, best open-source ~28%.
- Consequence: heavily occupies paired real-image intervention evaluation (our RealityBench space); also independently evidences that naive single-variable interventions often fail — motivation for SC2.

### CG-World

- Paper: https://arxiv.org/abs/2607.26452
- VERIFIED with precision 2026-08-24 (Table 3): exactly **5,000 strict mechanism + 5,000 strict action counterfactual branches**, 1,000 same-root families, invariant sets recorded; strict-CF criteria preserve exogenous context.
- Access caveat: dataset gated on paper acceptance; noncommercial license; raw source data under controlled access. **Not usable as our evaluation infrastructure today.**

### CWMDT

- Paper: https://arxiv.org/abs/2511.17481 (Shen et al., 2025-11-21)
- VERIFIED 2026-08-24. Counterfactual world models via LLM-edited digital twins conditioning video diffusion; open-loop, editing/reasoning-based; SOTA on two CF benchmarks.
- Consequence: owns editing-based CF video generation lineage; we must differentiate via coupling + interactivity.

### Genie 3 (capability claim only)

- Official source: https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/ ("Promptable world events", 2025-08-05)
- VERIFIED 2026-08-24 that the claim exists: mid-rollout text events alter weather/spawn objects, explicitly framed as enabling "counterfactual, or 'what if' scenarios"; limited research preview; events "not necessarily performed by the agent itself."
- Closed system: no checkpoints/inference path; capability unusable for research; cited only to fence off the intervention-capability claim.

### EVOKE

- Paper: https://arxiv.org/abs/2608.13546
- Code: https://github.com/AlayaLab/Evoke
- Model: https://huggingface.co/AlayaLab/Evoke
- Code-inspected facts (2026-08-24 audit, not yet executed by us): `MODE=segment` consumes `schedule_*.json` for scheduled per-chunk re-prompting during ongoing generation (switch granularity = chunk boundary); `SEED` exposed as run-level launcher knob; camera-indexed point-cloud world-state bank with write/read/evict (`GEO_HIST_MAX_FRAMES` eviction affects comparability); **no upstream branch/fork API**; partial replay via v2v re-seeding and `run_info.json`.
- Critical caveat: released distilled models were trained on v2v conditioning; distilled i2v/t2v are zero-shot. The stage-1 camera-control model is the released path with all conditioning modes in-distribution.
- Environment caveats: `diffusers` pinned to a dev fork not on PyPI; **both depth backends (ViGeo AND Depth-Anything-3) are CC-BY-NC-4.0** — noncommercial despite Apache-2.0 repo; 14B path reported 384×640@24fps, 2.11 s/chunk on H200 (~56 GB bf16 teacher sampling).
- License caveat: repo Apache-2.0, but required depth components are noncommercial. Audit before any commercial framing.

### Yume / Yume-1.5

- Paper: https://arxiv.org/abs/2507.17744 (Yume-1.5 also arXiv:2512.22096, CVPR 2026)
- Code: https://github.com/stdstu12/YUME
- Project: https://stdstu12.github.io/YUME-Project/
- Relevant idea: image-conditioned interactive world generation with quantized camera controls and autoregressive memory.
- Mid-rollout event-switching implementation status UNVERIFIED (paper encodes Event Description "only during the initial generation phase"). Verify released code before relying on it.
- Why we care: lower-risk first validation candidate before heavier research backends.

### RLVR-World

- Paper: https://arxiv.org/abs/2505.13934
- Relevant idea: post-train world models against verifiable decoded-output metrics rather than only likelihood.
- Use for us: methodological justification for reward-driven post-training, not proof that our proposed reward will work.

### PersistWorld

- Code: https://github.com/Jai2500/PersistWorld (repo fetch-verified 2026-08-24 by orchestrator; MIT; badge claims ECCV 2026 acceptance — venue self-reported at official repo)
- Paper identifier reported by model resources: arXiv:2603.25685
- Relevant idea: RL post-training branching K=16 continuations from a frozen shared context (group-relative optimization over own rollouts; multi-view visual rewards LPIPS/SSIM/PSNR).
- Use for us: evidence that rollout-level RL can matter; POST-SC1 stretch context only.

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
