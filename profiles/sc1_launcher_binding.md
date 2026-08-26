# SC1 Launcher Binding Contract (FINAL CPU ROUND 2026-08-26)

Scope: how a launcher binds a GPU/CPU run to the audited patch/profile/config
triple, and how the strict CPU RNG (condition B) is seeded. Everything here is
enforced mechanically by `harness/strict_coupling.py` (validator) and
`harness/sc1_preflight.py`; this document is the human-readable contract.

## 1. Launcher-exported identity environment

The launcher exports, per run:

| Env var | Source | Consumed by |
|---|---|---|
| `EVOKE_STRICT_PATCH_SHA256` | `patches/evoke-74d26851-strict-coupling.patch.sha256` sidecar (sha256 of the patch bytes) | emitter meta `patch_sha256` |
| `EVOKE_STRICT_PROFILE_SHA256` | sha256 of `profiles/sc1_strict_profile.json` bytes | emitter meta `profile_sha256` |
| `EVOKE_STRICT_CONFIG_SHA256` | **config identity** (formula below), computed by preflight over RESOLVED engine arguments + strict-relevant env | emitter meta `common_config_sha256` |
| `EVOKE_STRICT_CONFIG_SHA_ENGINE` | optional: same config identity recomputed inside the engine process from resolved argv when available; copied to meta `engine_resolved_config_sha256` (advisory evidence that launcher and engine resolved the SAME arguments) | emitter meta |
| `EVOKE_STRICT_BASE_SEED` | the resolved `--seed` integer passed to infer_single | strict CPU RNG derivation (condition B) |
| `EVOKE_WARP_SEED` | PRECOND-1 fixed derived value | da3_cloud covis isolated generator |

### Config identity formula

```
common_config_sha256 = sha256( canonical_json({
        resolved_infer_single_argv_minus_prompt_fields,
        infer_batch_env_exports_used_by_recipe_path,
        EVOKE_WARP_SEED_value,
    }) )
```

implemented as `sc1_preflight.canonical_config(resolved_args)` (prompt-only
fields excluded; negative prompt NOT excluded). Both branches MUST hash equal;
the validator fails the pair otherwise (`META_MISMATCH:common_config_sha256`).

## 2. Launch-strict mode

Set `launch_strict: true` in the pair manifest OR export
`EVOKE_STRICT_LAUNCH=1`. Archive GPU-01 pair manifests MUST record the literal
`"launch_strict": true`; missing, `false`, or `null` is refused by
`refuse_gpu_countersign()`. Routine local `TEST_MODE_ONLY` fixtures may omit it.
Effect (validator): literal `UNDECLARED` — or the
local-CPU marker `TEST_MODE_ONLY` — in ANY of `patch_sha256`,
`profile_sha256`, `common_config_sha256`, `diffusers` (either branch meta)
yields `INVALID` with reason `IDENTITY_UNDECLARED:<field>:<role>`. A missing
value counts as undeclared. Launch-strict mode additionally relies on the now-
mandatory pair-manifest ledger-artifact bindings:
`artifacts.factual_log.sha256` and `artifacts.counterfactual_log.sha256`
(checked for EVERY pair since this round; see `PAIR_MANIFEST_ARTIFACT*`).

## 3. TEST_MODE_ONLY and GPU countersigning

A CPU box without diffusers may set `EVOKE_TEST_MODE_ONLY=1`; the emitter meta
then records `diffusers="TEST_MODE_ONLY"` instead of `"UNDECLARED"`. Such
ledgers prove harness plumbing only. `refuse_gpu_countersign(result_or_manifest)`
(harness/strict_coupling.py) returns True (REFUSE) whenever any identity field
carries `UNDECLARED` or `TEST_MODE_ONLY`, or the result already carries
`IDENTITY_UNDECLARED` reasons. **Ledgers carrying either marker can never be
countersigned for GPU-01**; GPU-01 evidence must come from launch-strict runs
with real identity hashes.

## 4. Strict CPU RNG policy (condition B)

Upstream never seeds the DEFAULT CPU generator; two OS processes diverge.
Under StrictCoupling only, at the FIRST fork-hook invocation (= rollout start:
top of chunk iteration 0, before prompt selection/warp render/any R-site draw;
all audited stochastic sites use explicit generators and every default-CPU
consumer is forced off under the frozen profile) the patched engine runs:

```
seed64 = int( sha256("causalfork/sc1-strict-cpu-rng@1|pin=<pin>|base_seed=<bs>|"
                     "fork_chunk=<c>|pair_id=<pid>").hexdigest()[:16], 16 )
cpu_gen = torch.Generator(device="cpu"); cpu_gen.manual_seed(seed64)
torch.set_rng_state(cpu_gen.get_state())     # DEFAULT CPU RNG ONLY
```

`<bs>` = `EVOKE_STRICT_BASE_SEED` or literal `"UNSET"`; `<c>` = fork_chunk;
`<pid>` = pair id. Branch identity is EXCLUDED, so factual and CF replay
processes initialize identically. CUDA global RNG and managed Generators are
never touched. Recorded per run: meta `strict_cpu_rng_policy`,
`strict_cpu_rng_seed`, `cpu_rng_sha256_after_init`, `cpu_rng_sha256_at_fork`;
the FORK_CAPTURE sidecar mirrors the block. The validator fails asymmetric
evidence (`META_MISMATCH:strict_cpu_rng_*`) and F10 boundary-digest inequality.

## 5. Live-state adapter (condition 1)

The patched `__call__` hunk builds an EPHEMERAL NON-OWNING `LiveStateView`
(`build_live_state_view(history_latents, total_generated_latent_frames,
geo_state, self, chunk_index=k, event_set_size=len(_event_set),
forced_off_flags={...})`) gated on `fork_mode_active()`, and passes THAT VIEW
to the fork hook. F-id -> live source map (audited pin line numbers):

| F-id | digest attribute(s) | live source (pin @74d26851) | lifetime | req |
|---|---|---|---|---|
| F01 | history_latents / history_latent_counter | function-local rolling buffer pipeline_evoke.py:2299 (created), consumed :2502-2504/:2738/:3019-3021; counter total_generated_latent_frames :2140/:2310/:2319/:3019 | __call__ locals, updated :3019-3020 each chunk end | REQ |
| F02 | prev_frame_pix / prev_frame_latent | geo_state["prev_chunk_last_frame"] :3088 (init :592); geo_state["prev_chunk_last_decoded_latent"] :2211 init / :3125 update | geo_state dict, per-chunk | REQ |
| F03 | geo_frame_bank | geo_state["frame_bank"] :587-591 (add :2245/:3118); FrameBank.entries frame_bank.py:28 | geo_state dict | REQ |
| F04 | geo_da3_bank.pts/.c2ws/.frames | geo_state["da3_bank"] :633; dicts da3_cloud.py:601/:602/:603 | DA3FrameBank instance | REQ |
| F05 | geo_da3_bank._pt_mask | da3_cloud.py:606 | DA3FrameBank instance | REQ |
| F06 | geo_da3_bank._probation/_carve_strike/_win_hist/_pinned_wins | da3_cloud.py:530/:557/:598/:597 | DA3FrameBank instance | REQ |
| F07 | _geo_persist_feat_map / _geo_persist_feat_map_conv_idx | self._geo_persist_feat_map pipeline_evoke.py:467/:473/:516/:3044; conv idx = vae._conv_idx :474/:502/:507 | pipeline-persistent between chunks | REQ |
| F08 | counters_set | da3_cloud.py:538 (_ingest_calls) /:599 (_sr_ingests) /:600 (_sr_last) /:577 (_ca_seen); pipeline_evoke.py:457-464 (_decode_dump_idx, 0 while env off) | live counters, snapshotted into a scalar dict at build | REQ |
| F09 | estimator_stream_digest | ViGeo stream scalars vigeo_cloud.py:340 (_scale_locked)/:152+:338 (_anchor_scales); kv-cache `_kv` EXCLUDED (F15). sha256 over canonical JSON of {class,_scale_locked,n_anchor_scales,process_res} | computed read-only at build | ADVISORY |
| F10 | global_cpu_rng_sha256 (+ meta policy block) | torch default CPU generator state; seeded per section 4 | process-global | REQ |
| F11 | _geo_cfg_mirror_K_pix/_stride/_lag | geo_state["da3_K_pix"]:724 / ["da3_pix_stride"]:725 / ["da3_lag"]:730 | geo_state dict | REQ |
| F12 | generators evidence | collect_generators(main, _geo_patchdrop_gen) -> .get_state() sha256s | managed Generators | REQ |
| F13 | _geo_source_image_sha / _geo_i2v_flag_assert / _geo_anchor_pix_idx_assert / event_set_empty_assert | geo_state["source_image_pixel"]:590/:2231 (sha256 at build); ["da3_is_i2v"]:2289; ["v2v_chunk0_anchor_pix_idx"]:2232; len(_event_set)==0 with _event_set defined :2002 | config assertions (camera cursor is k+event_set-derived -> assertion, not state) | REQ |
| F14 | _geo_forced_off_flags | __call__ locals use_kv_cache:1825/use_cfg_zero_star:1780/use_dmd:1784/use_adaptive_anti_drifting:1788/use_interpolate_prompt:1765/geo_disable_prev_short:1798/is_keep_x0:1773 + self._short_tier_noise_cfg.enabled (:2330-2336) | captured per boundary | REQ |
| F15 | kv-cache/scheduler/_cgen/print counters | deliberately NEVER walked | - | EXCLUDED |

Residual honesty note: `restrict_self_attn` and `invisible_history_noise` are
not visible inside `__call__` scope; they remain PREFLIGHT-side assertions
(sc1_preflight.FORBIDDEN_RULES), not F14 entries.

`_short_tier_print_count` is intentionally excluded from F08. Source audit
finds it serves progress/logging only, with no generation-state consumer; it
cannot establish or break causal boundary equivalence.

## 7. cuDNN and flash-attn bring-up

Before model construction, the launcher records `torch.backends.cudnn.benchmark`
and `.deterministic` in `harness/env_fingerprint.py`. Set them to `False` and
`True`, respectively, before loading the model. These are deterministic-mode
hints, not a guarantee for every kernel or estimator implementation.

Run `python harness/flash_attn_preflight.py` before importing/loading any model.
An import or version failure reports `ENV_BRINGUP_FAILURE`; it is an environment
bring-up failure, never an SC1 coupling verdict.

## 6. Lazy-meta continuation rewrite (condition 4/E)

`_patch_meta_continuation` no longer swallows failures: any error emits a
`{"event":"META_PATCH_FAILURE", ...}` ledger line, clears the module flag, and
raises -> run aborts; the validator maps the marker to INVALID
(`META_CONTINUATION_UNVERIFIED`). Documented single-writer truncate-on-crash
window lives in that function's docstring.
