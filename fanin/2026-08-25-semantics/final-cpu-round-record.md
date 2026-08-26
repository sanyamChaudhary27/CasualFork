# Final CPU Round Record — Live-State Adapter + F10 + Hardening (2026-08-25)

Base: 27a8e53 · NO GPU. Closes review-record conditions 1–4 + F10 CPU-default-RNG blocker.

## A. LiveStateView (real EVOKE fork-state adapter)
Ephemeral non-owning view built at the top-of-chunk-loop boundary inside the patched `__call__`, passed to `maybe_fork_boundary` INSTEAD of the raw pipeline; constructed only when StrictCoupling active. Mapping audit (full table in profiles/sc1_launcher_binding.md §5, all source-cited at pin 74d26851):
F01 history_latents+counter ← __call__ locals (:2299/:3019–20) · F02 prev_frame_pix/latent ← geo_state (:3088/:3125) · F03 geo_state["frame_bank"] (:587–591) · F04 DA3 pts/c2ws/frames (da3_cloud:601–603) · F05 _pt_mask (:606) · F06 _probation/_carve_strike/_win_hist/_pinned_wins (:530/:557/:598/:597) · F07 _geo_persist_feat_map + vae._conv_idx (:467/:473/:516/:474/:502) · F08 counters (:538/:599/:600/:577/:2328+:2716/:457–464) · F09 ADVISORY estimator scalars (vigeo:340/:152) · F10 default-CPU RNG state · F11 K_pix/stride/lag (:724/:725/:730) · F12 managed generator evidence · F13 source_sha:2231/i2v:2289/anchor:2232/event_set:2002 · F14 forced-off locals · F15 excluded.
Mandatory tests PASS: complete view → missing_required_paths == []; deleted REQUIRED field → loud failure.

## B. F10 policy
Under StrictCoupling only, before rollout: derived strict CPU seed = int(sha256("causalfork/sc1-strict-cpu-rng@1|pin|base_seed|fork_chunk|pair_id")[:16],16); explicit CPU Generator + torch.set_rng_state() (CPU-only; managed CUDA/main generators untouched). Recorded: strict_cpu_rng_seed, cpu_rng_sha256_after_init, cpu_rng_sha256_at_fork. First-hook invocation ≡ rollout start because every default-CPU consumer is forced off under the frozen profile. Tests 1–4 implemented and passing (equality across process-equivalent inits; mismatch detection; main-generator immutability; gates-off no-op). No ADVISORY downgrade requested.

## C. Condition 2 closed
_safe_int meta parsing → META_MISMATCH on malformed/None fork_chunk (+ malicious fixture).

## D. Condition 3 closed
Launch-strict mode: literal UNDECLARED patch/profile/config/diffusers identities → INVALID(IDENTITY_UNDECLARED), one fixture per field; pair manifest carries both ledger artifact hashes; launcher binding documented (profiles/sc1_launcher_binding.md): export EVOKE_STRICT_{PATCH,PROFILE,CONFIG}_SHA256; config identity from resolved engine args via preflight canonical_config; TEST_MODE_ONLY marker exists for diffusers-less local runs and refuse_gpu_countersign() hard-fails such ledgers — impossible to countersign for GPU-01.

## E. Condition 4 closed
_patch_meta_continuation: silent except-pass removed; failure emits META_PATCH_FAILURE event + META_CONTINUATION_UNVERIFIED validator invalidation (strict certification aborts); truncate-on-crash window documented (single-writer). Forced-failure test passes.

## G. Verification matrix (orchestrator-run)
harness 8/8 · ledger-v1 12/12 · real-class 9/9 · v2 semantic 37/37 (extended from 22) · apply-check CLEAN on fresh pin extract (+1227/−1 hunk lines; sha256=44841f4afed3c161dd0d1e6ee952b53868fb0f2d64463dc270bce2ce6ea9456e) · byte-neutrality re-proven post-adapter (BN case in suite) · manual order proof: build_live_state_view precedes maybe_fork_boundary in the chunk-loop hunk and the view reflects post-prefix state.
