# Fix-Round Record — StrictCoupling v2 (2026-08-25)

Base: 5d21773 · Implements fanin/2026-08-25-semantics/adjudication.md + prior conditions 1–2 (+7 hygiene) + user mandate targets 1–12.

## Implemented
- Validator v2 (harness/strict_coupling.py): self-pair/same-source rejection; explicit branch roles; distinct run_ids; single meta header; full meta comparison (pin/patch/profile+content/torch/diffusers/warp_seed/config/fork_chunk); FORK_CAPTURE + GENERATOR_STATE_RESTORED event verification at fork_chunk; pair-manifest binding with artifact hashes; unique-ledger-per-run enforcement (existing-file refusal).
- Site-aware comparison modes per adjudication: R1/R4/R5/R6 EXACT_TENSOR; R2/R3 STREAM_WITNESS + diagnostics (sha256 input-pixels/mean/std; byte-equal at fork chunk; diagnostic-only after explained divergence); R7 ISOLATED_STREAM_WITNESS (per-draw _cgen state chain + high + skip flags; index tensors never compared).
- Per-chunk grammar from RE-AUDITED source order R7→R2→R3→R4→R5→R1→R6×2 (v1 prose was wrong about R7 position); fixed-site multiplicity + order enforced (GRAMMAR_* codes).
- True fork boundary in patch: hook at TOP of chunk loop before prompt selection/warp/all draws; stage context reset None at chunk start.
- FORK_STATE_DIGEST v1 (F01–F15 spec): capture at boundary; child recompute + compare BEFORE any post-fork draw; mismatch → FORK_STATE_MISMATCH event + hard abort; child digest written as FULL manifest (lazy-meta + canonical-dump bugs fixed).
- SC1 preflight (harness/sc1_preflight.py): forbidden options → abort; PRECOND-1/PRECOND-2 mechanical checks; config/profile/input/pose/checkpoint hash emission; prompt-only drift detection (rng_relevant_change flag).
- Profile JSON: BOM removed; plain utf-8 load test; schema validation test.
- Ledger isolation: run_id/pair_id on every line; existing-file refusal; env fingerprint module (python/torch/cuda/GPU/diffusers/transformers/patch-sha/pin).
- Docs: window(33) vs stride(36) distinction corrected; fork identity chunk-index-based.

## Verification matrix (all orchestrator-run this session)
| Suite | Result |
|---|---|
| Original model-free harness | 8/8 PASS exit 0 |
| Strict-ledger v1-updated | 12/12 PASS exit 0 |
| Real-class EVOKE state (pin imports) | 9/9 PASS exit 0 |
| V2 semantic suite (attacks A–P + grammar + preflight + digest + live end-to-end O + byte-neutrality BN + profile P) | 22/22 PASS exit 0 |
| Patch builder + apply-check on fresh pin extract | CLEAN, applied tree byte-identical |
| COMPANY_STATIC_OK | pass |

Patch: +842/−1 hunk lines across 3 files (pipeline_evoke.py, da3_cloud.py, new evoke/strict_fork.py), sha256=7e4dcd61f2efac3a…

## Defects found & fixed during integration (beyond the 4 fixture bugs)
1. _next_seq() deadlock: shared _LOCK re-acquired inside log_draw → dedicated _SEQ_LOCK.
2. Event lines lacked seq → shared monotonic line counter for draws+events (ordering proof expressible); reset_for_tests resets it.
3. Child FORK_STATE_DIGEST written via digest_canonical (missing manifest_sha256) → CHILD_DIGEST_CORRUPT; now full-manifest dump matching fsd.save convention.
4. Lazy meta continuation never set on live restore path → _patch_meta_continuation() rewrites header after successful restore.
5. Test O manifest used fixture warp-seed constant vs real env-derived sha → override with true digest.

## Known residuals (disclosed to reviewers)
- diffusers not importable locally → meta diffusers field UNDECLARED locally; validator handles gracefully; G1 must pip freeze.
- F09 estimator advisory equivalence deferred to O4 (per adjudication).
- FORK_STATE_DIGEST engine-local wiring (history_latents function-local upstream) is a G1 integration task; capture fails LOUDLY on missing REQUIRED fields by design.
- VRAM figures remain upstream-reported until G0 measurement.
