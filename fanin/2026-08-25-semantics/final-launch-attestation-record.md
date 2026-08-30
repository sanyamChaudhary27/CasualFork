# Final GPU-01 Launch-Attestation Correction (2026-08-26)

Base `9c0222033a2e205697048ccdbedcc663444d35e1`; no GPU, weights, dependency installation, or model construction.

- Shared schema `causalfork/gpu01-config-identity@1`: all resolved args common except explicit prompt/branch/output classifications; audited strict env included. Harness source is copied byte-identically to `evoke/gpu01_config_identity.py`.
- `harness/gpu01_launch.py` resolves exact argv, computes config, runs preflight, writes `causalfork/gpu01-prelaunch@1`, binds it to the manifest, and only then invokes exact argv with `shell=False` and sealed env.
- Patched `infer_single.main` calls `attest_engine_config(vars(args), os.environ)` immediately after real `parse_args`, before `_check_prereqs` and model construction. It recomputes config, rejects stale declarations, requires/binds PASS prelaunch evidence, ignores operator `EVOKE_STRICT_CONFIG_SHA_ENGINE`, and records engine SHA plus prelaunch artifact SHA.
- Launch-strict validator requires factual/counterfactual prelaunch path+SHA and binds PASS status, pair/run/role, pin, patch/profile/config, argv structure, ledger engine/common config, and ledger archive SHA.

Evidence: 8/8, 12/12, 9/9, 76/76; COMPANY_STATIC_OK; L1–L12 PASS; gates-unset byte-neutrality PASS; fresh-pin apply-check CLEAN and applied tree byte-identical. Patch `ee25e02c479c21aa214e630f8165fd67b6d7bc10f1f0c30ac4b06786fd920970`, +1538/−1, 1674 lines. GPU-01 remains NOT EXECUTED / review pending.
