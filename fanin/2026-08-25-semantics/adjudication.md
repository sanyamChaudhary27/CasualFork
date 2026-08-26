# Sealed Three-Way Adjudication — Coupling Semantics (2026-08-25)

Base: 5d21773 · Seal order A→B→C simultaneous, mutually blind.
A stochastic semantics ses_fc66255b… · B validator adversary ses_fc6622dc… · C fork-state ses_fc661f1e…

## Adjudicated site comparison policy (binding for implementation)

| Site | Class | Required witness | Must hold | Must NOT be required |
|---|---|---|---|---|
| R1 (:371) | EXACT_EXOGENOUS_TENSOR | tensor_sha256(noise) | tensor equality | — |
| R2 (:424) | STATE_DEPENDENT_REPARAM | gen-state bracket around sample(); diagnostics sha256(warp-input pixels), sha256(mean), sha256(std); ε=(z−mean)/std recoverable | state-chain equality + shape/count; fork-chunk input-hash byte-equality | z-tensor equality post-divergence |
| R3 (:432) | STATE_DEPENDENT_REPARAM | same as R2 | same | same |
| R4 (:976–978) | EXACT_EXOGENOUS_TENSOR (affine-invertible σ=uΔ+σmin) | tensor_sha256(sigmas) | sigma equality ⇔ innovation equality | — |
| R5 (:996) | EXACT_EXOGENOUS_TENSOR | tensor_sha256(pre-mixing noise) | tensor equality | post-mix output equality |
| R6 (:573) | EXACT_EXOGENOUS_TENSOR (injective ε@Lᵀ) | tensor_sha256(noise) | noise equality | — |
| R7 (:1486–87) | STATE_DEPENDENT_DISCRETE | per-draw _cgen get_state() before/after chain (fresh seed per render call); high=wp.shape[0]; within-call ordinal; skip flags | chain equality up to first EXPLAINED domain-size/skip divergence; PRECOND-1 export | index-tensor equality; cross-call chain beyond first explained divergence |

## Validator rulings (Auditor B, all confirmed)
Self-pair/copy PASSes today; symmetric missing/truncation PASSes; meta/events/pin/warp_seed never checked; branch-role swap PASSes; global_rng CPU-only + field-strip bypass; R7 rows exempted from stream checks; multi-meta hijack possible. v1 verdicts barred from gate evidence. v2 mandatory: self-pair guard, roles, distinct run_ids/pair_id, single meta header, full meta comparison (pin, patch SHA, profile SHA, torch/diffusers, warp seed, common config, fork chunk), event validation (FORK_CAPTURE/GENERATOR_STATE_RESTORED at fork_chunk), lazy-meta fix, pair-manifest+artifact binding, unique-ledger-per-run (no silent append).

## Fork-state ruling (Auditor C, adopted)
Prefix hash + RNG restore = necessary, NOT sufficient. FORK_STATE_DIGEST v1 (fields F01–F13 REQUIRED: history_latents+counter, prev frame+latent, FrameBank entries, DA3 pts/c2ws/frames/_pt_mask+keysets, _probation/_carve_strike, counters set, _geo_persist_feat_map(+_conv_idx), config mirrors/K_pix/stride/lag, estimator stream digest ADVISORY→REQUIRED post-O4, main generator state+global CPU sha, source/K/i2v/anchor/event_set=∅ config assertions; F14 forced-off flags asserted; F15 excluded: kv-cache/scheduler/_cgen/print counters). SHA-256 over raw contiguous bytes with "shape|dtype|" prefix (byte-compatible with tensor_sha256); canonical sorted-key manifest; cross-process protocol = parent captures digest+blobs, child replays 0..c*−1 from seed, compares BEFORE any chunk-c* draw; REQUIRED mismatch → abort + FORK_STATE_MISMATCH ledger line.

## Fork-boundary mechanics
Hook relocates to TOP of chunk loop (before prompt selection, warp render, any R-site draw); stage context reset to None at chunk start; regression test must prove zero R-site draws occur before restore at the fork chunk.

## Additional facts frozen
diffusers 0.39.0 sample() form VERIFIED (AutoencoderKLWan → DiagonalGaussianDistribution; vendored copy absent; pip freeze must be captured at G1). R7 consumption range-independence verified on torch-cpu. _geo_persist_feat_map included in digest (cross-process bitwise regeneration UNVERIFIED until G0 rerun delta). Camera cursor derived from k+event_set → config assertion, not state. warp_history_prefix_latent dead code (written never read).
