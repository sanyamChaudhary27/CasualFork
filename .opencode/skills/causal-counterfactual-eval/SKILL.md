---
name: causal-counterfactual-eval
description: Use when scoring a factual/counterfactual branch pair - writes the intervention contract first, then checks invariants, shared prefix/camera/noise policy, minimal-change locality against simulator ground truth or paired human review.
---
# Counterfactual Evaluation

Before scoring, write the intervention contract:

- what is deliberately changed;
- what must remain invariant;
- what downstream changes are logically allowed;
- whether prefix, controls, and noise are exactly shared or only approximately matched.

For synthetic scenes, compute against simulator truth: changed-object/region masks, depth, segmentation, camera matrices, state variables.

For real scenes, combine geometry/features with human paired review. Use learned VLM/CLIP judges primarily for semantic adherence, not as the sole proof of causal locality.

Report a vector: intervention, identity, geometry, temporal, camera, locality, artifacts. Reward weights must be disclosed.
