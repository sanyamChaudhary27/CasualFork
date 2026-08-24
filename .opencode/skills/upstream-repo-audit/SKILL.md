---
name: upstream-repo-audit
description: Use BEFORE integrating any upstream ML repository or pretrained model - verifies checkpoint availability, official minimal inference command, conditioning mode, dependency pins, reported VRAM/runtime, licenses of repo and model components, then outputs a go/no-go table.
---
# Upstream Repository Audit

Before integrating a model:

- record URL and commit/revision;
- identify the exact released checkpoint needed;
- find the official minimal inference command;
- verify conditioning mode and data format;
- inventory non-PyPI forks, compiled extensions, external binaries, and separate weights;
- record Python/PyTorch/CUDA pins;
- find reported GPU model, VRAM, RAM, resolution, steps, and runtime;
- inspect known caveats in README/model card/issues when material;
- audit licenses of the repo **and required model/depth/base components**;
- list files we must change versus keep pristine.

Output a go/no-go table plus the first reproduction command.
