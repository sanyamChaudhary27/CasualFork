# GPU Experiment Proposal — GPU-01

**Status: DRAFT — NOT EXECUTED. Requires reviewer countersignature before launch (COMPANY.md GPU experiment proposal gate).**

## Required fields (per COMPANY.md)

- **Research question:** Can we reproduce one official EVOKE generation and then produce one short controlled twin continuation using the validated fork mechanism? (Colab-first; this is G1 + the first strict-coupled branch proof, nothing more.)
- **Hypothesis:** With the GF0 patch set applied to pinned tree `74d268516d95c8fceadd2378f91a73f9f187042b` — generator-state capture/restore at pipeline_evoke.py:2791/:1333, an in-call fork switch modeled on the event_chunks machinery, and draw-log instrumentation per the harness contract — two continuations from one forked prefix under byte-identical configs (prompt-schedule-only divergence) will show per-chunk pre-model noise-tensor hash equality (mode A), while a fresh-RNG control branch will show inequality (mode B).
- **Decision affected:** Whether SC1 proceeds on EVOKE as backend (SPEC §2a strict-coupled achievable) or downgrades per the fallback rule; whether G1→G5 gates advance.
- **Cheapest falsification:** The O1 dual-run desync demonstration — same-seed runs differing only by an event chunk must produce unequal post-fork noise hashes; if instead our instrumentation cannot detect this, the coupling methodology is invalid. Second: shared-vs-fresh-instance comparison (O4); if outputs differ, state isolation fails and no branch claim is possible.
- **CPU alternative (done):** model-free harness, 8/8 tests PASS exit 0, independently reproduced 2026-08-24 (fanin/2026-08-24-gf0/fanin-record.md). Remaining CPU work before launch: execute Auditor B's deepcopy/eviction unit designs against real EVOKE classes; reviewed patch diff.
- **Colab alternative:** THIS IS the Colab experiment. T4/L4-class runtime acceptable for pipeline validation at reduced resolution/steps (EXPERIMENTS.md compute ladder); final fidelity explicitly not claimed.
- **Requested GPU / VRAM:** single T4/L4 (16–24 GB) for reduced-resolution run; EVOKE full path reports ~56 GB bf16 teacher sampling — if the distilled v2v path cannot fit, reduce resolution/chunk count and record honestly rather than switching backends mid-experiment.
- **Expected paid-GPU consumption:** ≤2 Colab GPU-hours total: 0.5 h environment bring-up (dev-fork diffusers install is the known risk), 0.5 h official-sample reproduction, 1 h twin-continuation runs (factual + mode-A + mode-B + desync demo).
- **Success criterion (predeclared):** (a) unmodified official sample produces visually sane output (G1); (b) twin branches from one fork point with byte-identical configs show draw-log equality up to fork AND per-chunk noise-hash equality after fork (strict-coupled per SPEC §2a); (c) mode-B control shows hash inequality; (d) O1/O4 falsification rides behave as predicted.
- **Failure criterion:** any of — official sample unreproducible after environment verification; post-fork noise hashes unequal despite restored generator state and identical configs; draw-log desync detected without a declared cause → downgrade that path to prefix-shared-seed-matched and trigger SPEC §2a fallback rule.
- **Artifacts to preserve:** environment report (G0 fields); exact commands + logs; pinned commit + our patch diff; per-chunk per-draw noise-tensor hashes for every branch; decoded-latent hashes via EVOKE_SAVE_DECODE_LATENTS; branch manifests in harness manifest format; all clips/latents under ignored artifacts dir with hashes recorded in EXPERIMENTS.md entry.
- **Reviewer countersignature:** PENDING — dispatch independent reviewer on this proposal + patch diff before any Colab GPU session starts.

## Constraints honored
No search, no RL, no product frontend, no Blender benchmark, no hero-seed hunting. One official generation, one controlled twin continuation. License note: both depth backends CC-BY-NC-4.0 — research-use only framing.
