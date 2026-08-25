# O1/O4 Falsification-Ride Pre-registration (frozen 2026-08-25)

Status: PROTOCOL PRE-REGISTERED before any GPU execution. These rides execute during the first capable GPU run, immediately after G1 official reproduction, BEFORE any SC1 measurement is counted. Preconditions from profiles/sc1_strict_profile.json: PRECOND-1 `EVOKE_WARP_SEED` exported (else R7 covis subsample silently uses global CUDA RNG); PRECOND-2 engine `.eval()` mode asserted at startup.

## O1 — DRAW-DESYNC POSITIVE CONTROL

- **Question:** does our coupling validator actually catch deliberate desynchronization? A false negative here invalidates every later STRICT_NOISE_COUPLED claim.
- **Construction:** run the standard forked twin protocol twice. Run 1 = strict protocol as designed. Run 2 = identical except ONE deliberately non-strict lever engaged post-fork, chosen from (ranked): (a) enable one event chunk after the fork (skips warp render+encode draws R2/R3 — expected ORDINAL_MISMATCH/MISSING_SITE); (b) flip visibility-aware warp noise off (R5 replaced by dormant uniform sibling draw — expected UNEXPECTED_SITE/TENSOR_MISMATCH); (c) unset `EVOKE_WARP_SEED` (R7 falls to global RNG — expected PRECOND1_GLOBAL_RNG_BYPASS via role GLOBAL_FALLBACK).
- **Expected result:** `compare_coupling_logs` returns STRICT_COUPLING_INVALID with the specific machine-readable reason code(s) matching the injected lever, for each lever tested.
- **Falsification of OUR instrument:** any O1 run returning STRICT_NOISE_COUPLED ⇒ instrumentation is broken ⇒ SC1 stops immediately and GF0 reopens. This is a positive control: it must fail to couple.

## O4 — PIPELINE-INSTANCE LEAK CONTROL

- **Question:** is carefully-restored shared-instance execution equivalent to isolated-instance execution under the strict protocol (no unaccounted mutable-state difference)?
- **Construction:** A = factual→CF branches executed sequentially on ONE pipeline instance with the patch's capture/restore protocol. B = the same CF branch executed on a fresh/isolated pipeline instance built from identical config. Feasibility note: a second resident pipeline ≈ doubles ~28 GB VRAM (upstream `_PIPE_CACHE` comment, infer_single.py:1097); if the runtime cannot host B alongside A, execute B as a separate process/run from identical artifacts and say so in the manifest.
- **Expected result:** no unaccounted state-induced difference — identical noise ledgers post-fork (modulo declared branch_id fields) and latent-hash equality within kernel-nondeterminism tolerance declared up front.
- **Blocking rule:** ANY unexplained A-vs-B difference blocks SC1 until root-caused and either fixed or explicitly attributed (with evidence) to declared kernel nondeterminism.

## Accounting
Both rides' logs and manifests are preserved as first-class artifacts. Neither ride's cost counts against SC1 sample budgets. If O1 or O4 fails, no SC1 locality numbers produced in that session are admissible.
