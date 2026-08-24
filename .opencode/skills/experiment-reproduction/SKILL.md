---
name: experiment-reproduction
description: Use when creating or reviewing any ML experiment so it can be rerun from its manifest alone - captures git commits, environment, input hashes, controls, camera trajectory, seeds/noise, metrics, hardware/VRAM, artifact hashes, and one predeclared pass/fail gate.
---
# Experiment Reproduction

Every experiment gets an ID and manifest. Capture:

- project commit;
- upstream revision/checkpoint;
- hardware + software versions;
- command/notebook cell range;
- all generation controls;
- source input hash;
- prompt/intervention;
- camera trajectory;
- RNG/seed/noise policy;
- runtime/peak VRAM;
- output artifact paths and hashes;
- metric vector;
- pass/fail gate.

Reproduction test: a fresh session should be able to read the manifest and produce the same configuration without asking what parameters were used.
