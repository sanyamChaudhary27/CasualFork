# StrictCoupling Pre-GPU Implementation Review — Sealed Dual Review Record (2026-08-25)

Base commit: 921d482. NO GPU authorized or used. Seal order: REVIEWER-1 (gpu-engineer) and REVIEWER-2 (reviewer) dispatched simultaneously in one message, mutually blind.

| Reviewer | Session | Verdict | Confidence |
|---|---|---|---|
| R1 gpu-engineer | ses_fc697110affe3CCz3d6EIDm4TC | PATCH_READY_GPU01_READY | high |
| R2 reviewer (adversarial) | ses_fc696d676ffe6jLeAEQ59zuFLF | PATCH_INCOMPLETE | medium-high |

## R1–R5 agreement matrix

| Question | Agreement |
|---|---|
| R1 false STRICT_NOISE_COUPLED? | Split: R1 "hardened well" w/ unsigned-JSONL caveat; R2 found concrete vacuous-pass paths |
| R2 untracked sites? | Both re-grepped: 7-site reachable set CONFIRMED by both; R1 found 4 unlisted v2v-block expressions (:2105–2129, unreachable under i2v); R2 found randperm :290 (training-only); both = inventory bookkeeping, not reachability threats |
| R3 alias/leak? | Both: restore path generators-only; isolation rests on fresh-process discipline + O4 backstop; real-class tests cover toy-injected banks only — ViGeo/estimator internals remain GPU-verified-later |
| R4 GPU-01 hardware evidence? | BOTH CONFIRM against source: 28 GB resident (:1097), 50.4 GB peak/worker (infer_post_distill.sh), no inference offload upstream, T4/L4 removal correct, ≥80 GB target justified, capacity-gate sound. Caveat: VRAM figures upstream-reported pending G0 measurement |
| R5 minimality? | Both: +447/−0 additive, env-gated early-returns, zero RNG-consumption change when off, apply-check CLEAN — still evaluating EVOKE |

## Adjudicated disagreements (orchestrator)

1. **Validator same-file vacuous pass** (R2 major): `compare_coupling_logs(f, f)` returns PASS; branch_id not in compared fields; meta lines parsed-then-discarded; lazy-meta leaves restored_branches empty on live runs. VERIFIED REAL → must fix (validator v2) before any GPU claim.
2. **Fork-hook placement** (R2 major): hook at prepare_latents (~:2810) fires AFTER chunk-c* warp draws R2/R3/R4/R5/R7 — mid-chunk, contradicting profile's "fork at chunk boundary." Under replay-from-seed semantics harmless; under resume semantics the CF branch would consume pre-hook draws before restore → loud TENSOR_MISMATCH failure, not silent corruption. VERIFIED REAL AMBIGUITY → relocate hook to top-of-chunk-loop OR document resume semantics + parity assertion.
3. **GPU-01 staleness** (R2 major): hypothesis cited :2791/:1333 DMD capture + event_chunks-modeled switch — stale vs shipped patch (stage2 pyramid R6; event_chunks forbidden). Orchestrator documentation error → fixed in proposals/GPU-01 this commit.
4. **Inventory completeness** (both): addendum appended to sc1_stochastic_site_inventory.md (U12a v2v-block ×4 UNREACHABLE-i2v; U12b randperm UNREACHABLE-training-only; battery-extension requirement).

## Final adjudicated verdict: PATCH_INCOMPLETE

Basis: two independent validator false-positive paths and one boundary-semantics defect sit exactly in the machinery that would certify STRICT_NOISE_COUPLED. Fail-closed per constitution (UNVERIFIED ≠ PASS). GF0 status unchanged (FEASIBLE_WITH_PATCH); hardware plan confirmed evidence-backed by both reviewers (the NEEDS_HARDWARE_CHANGE component is already incorporated in revised GPU-01).

## Consolidated pre-GPU conditions (close ALL, then re-review delta)

1. Validator v2: distinct-file guard + matching branch labels required for comparison; compare meta lines (pin/torch/warp_seed/patch presence); validate FORK_CAPTURE/GENERATOR_STATE_RESTORED events at fork_chunk; fix lazy-meta continuation field; reject bare JSONL equality without manifest binding (common-config hash + artifact hashes).
2. Fork-hook relocation to true chunk boundary (top-of-chunk-loop) with regression test, or documented resume semantics asserting warp-draw parity at G1.
3. Inventory: keep ADDENDUM; extend future batteries with randperm|np.random|random. patterns (done in addendum text).
4. SC1/G1 branches run as separate OS processes per branch until O4 passes shared-instance equivalence.
5. G0 must measure actual pipeline VRAM residency (nvidia-smi) converting 28 GB author-comment into reproduced tier-1 number; assert no offload path activates; assert EVOKE_WARP_SEED exported (PRECOND-1) and all modules .training == False (PRECOND-2) from launch logs; same-seed rerun delta measured before byte-identical-prefix claims.
6. Mode-B control + O1 desync ride remain blocking success criteria (already pre-registered).
7. Minor ledger hygiene: open ledger with run-id header (stale-run mixing), restore-side torch-version check, document CPU-global digest limitation (CUDA-global detection via R7 GLOBAL_FALLBACK role).

## Exact next action
Dispatch experimenter fix-round closing conditions 1–2 (+7 hygiene), re-run all three suites, then a single delta re-review before GPU-01 countersignature.
