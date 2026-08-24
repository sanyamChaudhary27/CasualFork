# GF0 Sealed Mini-Panel — Fan-in Record (2026-08-24)

Research question (identical for all): can EVOKE expose/snapshot/clone/control all state required for meaningful future-noise coupling at a branch point?

| Seal # | Auditor | Agent type | Attempts | Session ID | Status |
|---|---|---|---|---|---|
| 1 | A RNG/diffusion | world-model-researcher | 1 | ses_fcb134dc9ffez8nQei7CzIPUmt | SUCCESS |
| 2 | B world-state fork | experimenter | 1 | ses_fcb0a01e7ffekSQOlUrUQHTCEf | SUCCESS |
| 3 | C protocol skeptic | reviewer→novelty-red-team | 3 (ses_fcb02937…, ses_fcb010202… INFRA_FAILURE ×2) | ses_fcaff89f9ffe5agIjpMCOl4hs9 | SUCCESS |

All pinned revision: AlayaLab/Evoke main tree `74d268516d95c8fceadd2378f91a73f9f187042b`.

## Convergent findings
1. Single CUDA `torch.Generator` (infer_single.py:1434) feeds ALL draws; schedulers fully deterministic (zero entropy).
2. Future-noise coupling architecturally supported via `get_state()/set_state()`; NO capture hook exists; minimal patch ≈10 lines at pipeline_evoke.py:2791 (per-chunk init noise) and :1333 (DMD per-step renoise).
3. Mid-rollout resume does not exist upstream; `geo_state`/banks internal to `__call__`; `event_chunks` machinery (:1441–1463) is a working template for mid-rollout divergence.
4. Deepcopy of branch state sufficient EXCEPT `da3_est` (share, never copy). Minimal fork serialization set: rolling history latents (+counters), `geo_state` minus estimator (both banks incl. side-state/counters, prev frame+latent, source pixel, K_pix, scalars), generator states + camera/event cursors, conditional extras (anti-drift stats, short-tier sigma, persistent feat map).
5. Shared pipeline instance leaks (`_geo_persist_feat_map`, `_short_tier_rollout_sigma`, `_short_tier_print_count`, global `_GEO_DEPTH_ESTIMATORS`) → branches need fresh instances or strictly serialized execution with restored state. Scheduler cross-branch leakage REFUTED (per-chunk set_timesteps resets history).
6. **Skeptic's decisive objection (O1, VERIFIED): draw count/order is content/flag-conditional** (event chunks skip ≥2 draws; anti-drift corruption is drift-triggered; warp-noise path branches on visibility). "Same seed" ⇒ identical future noise ONLY IF both branches consume identical draw sequences — i.e., byte-identical flags/config, prompt-schedule-only divergence.
7. Coupling must be asserted at logged pre-model noise tensors, NOT pixels or seeds: `--geo_chunk0_ref_warp` default-on is documented non-bit-reproducible; GPU kernels nondeterministic (no use_deterministic_algorithms).
8. Unseeded hazards: `_geo_maybe_noise_invisible_history` uses global-RNG `randn_like` (content-gated); `sample_block_noise(generator=None)` fallback nondeterministic.
9. Refuted attacks: CFG cond/uncond passes draw no randomness; latent shapes prompt-independent; prompt_schedule swaps embeddings only.
10. Observational confound (O5, reasoning-only): locality gain conflates coupling effect, intervention magnitude, drift rate — SC2 design must hold intervention strength fixed and measure drift baseline separately.

## Adjudicator-facing synthesis
Verdict candidate before Phase C/D: **GF0_FEASIBLE_WITH_PATCH**, contingent on (i) generator-state capture patch; (ii) byte-identical branch configs with prompt-schedule-only divergence; (iii) coupling asserted on logged noise-tensor hashes per chunk/step (draw-log equality up to fork; declared counted divergence after); (iv) isolated pipeline instances or serialized execution with full state restore; (v) honest labeling of chunk-0 ViGeo warp caveat. GF0_STRICT_FEASIBLE would require upstream-free bit-exact continuation evidence we do not have; GF0_SEED_MATCHED_ONLY would ignore that generator-state control genuinely exists in-code. Final call belongs to the Phase D reviewer.

## FINAL ADJUDICATION (Phase D)
Reviewer session ses_fcacfa8d1ffepWW7Gl6O5bjfWo returned: **GF0_FEASIBLE_WITH_PATCH**.
- Static line-by-line harness trace: 8/8 logically sound, none vacuous; caveats noted (toy-dynamics construction bias, rng_state_to_json gauss-truthiness edge, adapter-gap for arbitrary EVOKE objects).
- Dynamic confirmation satisfied by orchestrator's own run (this session): `python harness/run_tests.py` → 8/8 PASS, exit 0 (reviewer session lacked shell; gap disclosed).
- Seven residual risks/conditions attached (draw-log gate per sample; shared-vs-fresh-instance equivalence check; tensor-level coupling assertions only; global-RNG bypass ledger incl. `_wseed` audit; CC-BY-NC-4.0 depth backends — reviewer flagged license constraint beyond panel findings; B's deepcopy unit tests to be executed against real EVOKE classes).
- Required before GPU spend: archived harness log (done); reviewed patch diff vs pinned tree; CLAIMS.md updates; two pre-registered falsification rides on first G1 sample (O1 desync demo; O4 instance-leak comparison).
