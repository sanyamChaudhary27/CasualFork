---
name: colab-gpu-debug
description: Use when running or debugging GPU notebooks on Google Colab - records runtime hardware/software (nvidia-smi, PyTorch, CUDA, bf16), isolates dependency failures, proves the official sample at conservative settings before custom inputs, and separates pipeline validation from final-fidelity runs.
---
# Colab GPU Debug

At notebook start, print and save:

- `nvidia-smi` GPU/driver/VRAM;
- Python, PyTorch, CUDA runtime;
- bf16 support;
- RAM/disk;
- package versions and git commit.

Rules:

1. Do not assume T4/L4/A100 from the plan name.
2. Install dependencies in a clearly separated setup section.
3. Restart runtime only when a compiled/library change actually requires it; document the restart boundary.
4. Prove the official sample at conservative resolution before custom input.
5. Save logs/artifacts to a predictable directory before the runtime can disappear.
6. Treat Colab success as pipeline validation; do not force final-quality settings onto insufficient VRAM.
7. When a cell fails, preserve the exact exception and environment before patching.
