---
name: oom-recovery
description: Use when a CUDA out-of-memory (OOM, "CUDA out of memory") error hits a notebook or GPU script - walks a measured one-variable-at-a-time VRAM ladder while preserving the known-good baseline and tracking quality tradeoffs.
---
# OOM Recovery Ladder

Before changes, record peak allocated/reserved VRAM and the exact failing operation.

Then try one relevant change at a time, measuring after each:

1. release stale model/tensor references and verify no duplicate pipeline is loaded;
2. inference mode / no-grad / autocast correctness;
3. lower batch/candidate count;
4. reduce frames/chunk count;
5. reduce resolution to the next backend-valid multiple;
6. enable supported attention/memory-efficient path;
7. supported CPU/offload strategy;
8. quantization only if the model path officially tolerates it;
9. move to larger GPU.

Do not blindly call `empty_cache()` as a substitute for fixing live allocations. Never stack five memory changes and then claim which one helped. Record visual/semantic degradation for every memory-saving change.
