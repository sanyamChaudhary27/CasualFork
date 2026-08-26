# Final CPU Micro-Round Record (2026-08-26)

Base commit: `0c351188341aa34f78ee3bccc1038586f6681e83`. Scope: only the sealed final-review blockers plus predeclared validator hygiene. No GPU, download, install, model load, search, RL, or contract extension.

## Changes

- F13: i2v now reads the v2v anchor present-or-None. `None` digests as `N:` (not MISSING); i2v requires `da3_is_i2v=True, anchor=None`; v2v requires false + non-bool integer anchor. Bad combinations raise `F13_MODE_INCONSISTENT`.
- F12: capture requires named `generators["main"]` with usable nonempty state; failures are `F12_MAIN_GENERATOR_MISSING` or `F12_MAIN_GENERATOR_INVALID`; auxiliaries remain supplementary evidence.
- F10: capture/restore hooks refuse sidecar writes unless strict seed, post-init SHA, at-fork SHA, and non-null digest F10 exist and the boundary hash equals the at-fork SHA. Validator invalidates null/missing F10 evidence on either/both branches.
- GPU archival gate: `refuse_gpu_countersign` hard-refuses manifests/results whose archived `launch_strict` is not literal true.
- Hygiene: non-dict `warp_seed` produces `META_MISMATCH`; null/empty GPU-relevant manifest values reject; logging-only `_short_tier_print_count` excluded from F08; resolved cuDNN flags fingerprinted; flash-attn pre-model-load probe reports `ENV_BRINGUP_FAILURE`.

## Reproduced CPU evidence

| Command / check | Result |
|---|---|
| `python harness/run_tests.py` | 8/8 PASS |
| `python harness/test_strict_ledger.py` | 12/12 PASS |
| `python harness/test_real_evoke_state.py` | 9/9 PASS |
| `python harness/test_strict_ledger_v2.py` | 54/54 PASS, 0 blocked |
| `python scripts/verify_company.py` | `COMPANY_STATIC_OK` |
| `python patches/make_sc1_patch.py` | fresh-pin `git apply --check` CLEAN; applied tree byte-identical |
| gates-unset byte-neutrality | PASS (v2 `BN`) |

Patch: `c79a18cd44a3b8aef1a01349051b1f0c539fe80ce9ed4577c01b3eadac2ae563`, +1375/−1 hunk lines, 2024 patch lines. `flash_attn` is absent locally; the probe correctly returned `ENV_BRINGUP_FAILURE`, an environment status, not an SC1 result.

## New fixture coverage

F13-I1/I2/I3 and F13-V1/V2; F12 main-valid/empty/aux-only/invalid/main+aux; F10 capture boundary mismatch and both-null pair invalidation; launch-strict true/missing/false eligibility/refusal; null required manifest values; truthy non-dict warp seed; flash-attn classification. DG2 byte-compatibility and BN remain green.

## Gate status

CPU implementation evidence is reproduced but GPU-01 is **UNVERIFIED/PENDING SEALED DELTA REVIEW**. Countersignature is not granted by this record.
