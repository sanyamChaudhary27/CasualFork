# Final Validator / Launch-Guard Correction Record (2026-08-26)

Base: `68ccb535c161f7b71b9c480499951913ca59f28b`. Scope: D008 reversal conditions only. No GPU, download, package install, weights, model construction, or rollout occurred.

## CPU-proven corrections

- **F10 binding:** `validate_loaded_boundary_digest` independently validates each loaded parent/factual and child/counterfactual digest. F10 must be a valid SHA-256 and equal that run's `cpu_rng_sha256_at_fork`; cross-digest equality remains an additional check. Reproduced attacks F10-A through F10-E reject forged/null/mismatched evidence; F10-D passes valid equal evidence.
- **F12 artifact validation:** each loaded digest requires F12 object → generators object → valid named main (`status=OK`, SHA-256, non-bool positive integer `nbytes`). F12-D1 through D6 cover missing, no-main, auxiliary-only, invalid status/hash, and valid evidence.
- **JSONL:** scalar/list/null/bool JSON lines now become caught `LEDGER_PARSE_ERROR` invalidation, never `.get` crashes.
- **F08:** `_decode_dump_idx` removed after pin audit (`pipeline_evoke.py:457-464`): it only names/prints `EVOKE_SAVE_DECODE_LATENTS` dumps and has no generation consumer. Digest invariance fixture passes for states differing only in that counter.
- **Launch guard:** new CPU-testable `harness/gpu01_prelaunch.py` validates frozen GPU-01 identity/strictness/seeds/fresh IDs and flash-attn before model construction, writes one JSON status artifact, fingerprints the environment, and applies cuDNN hints. Patched strict process reapplies/records the hints in its own process. Hints are explicitly not a CUDA bitwise-determinism claim.

## Reproduced matrix

| Evidence | Result |
|---|---|
| model-free harness | 8/8 PASS |
| strict-ledger compatibility | 12/12 PASS |
| real EVOKE state | 9/9 PASS |
| v2 semantics | 64/64 PASS, 0 blocked |
| company static | `COMPANY_STATIC_OK` |
| patch generation | +1392/−1 hunk lines; 2041 patch lines |
| fresh pin / applied tree | `git apply --check` CLEAN; byte-identical |
| gates-unset byte-neutrality | PASS |

Patch SHA-256: `5bd2ffa9f892d4915ef2710e3b712445a96b968e6c95e39a93a4ec252b64f587`.

Local `flash_attn` probe correctly returned `ENV_BRINGUP_FAILURE` (`ModuleNotFoundError`); this is infrastructure evidence only. GPU-01 remains NOT EXECUTED and UNVERIFIED pending the final sealed review.
