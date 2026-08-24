---
name: world-model-evaluation
description: Use when evaluating interactive video world-model rollouts (any backend) - scores camera/control fidelity, frame quality, temporal coherence, identity drift, geometry, prompt adherence, latency, and peak VRAM on separate axes with the same serialized camera path.
---
# World Model Evaluation

Evaluate a rollout on separate axes:

- camera/control fidelity;
- frame-level visual quality;
- temporal consistency;
- long-horizon identity drift;
- geometry/depth consistency;
- revisitation consistency if the path returns to a place;
- prompt/intervention adherence;
- latency / generated-seconds-per-wall-second;
- peak VRAM and host RAM.

Use the same serialized camera path for backend comparisons. Do not average away a catastrophic axis. Preserve raw per-axis metrics and videos.
