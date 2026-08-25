# SC1 Stochastic Site Inventory (P2) — every random draw in the pinned tree

**Pin:** AlayaLab/Evoke @ `74d268516d95c8fceadd2378f91a73f9f187042b` (clone verified clean; read-only).
**Method:** fresh grep battery over the ENTIRE tree (no prior audit trusted): patterns
`randn_like|torch.randn|randn_tensor`, `torch.rand(|torch.randint|torch.normal|multinomial|bernoulli|exponential_`,
`latent_dist.sample|manual_seed|get_state|set_state`, `Generator`, `np.random|random-module usage`
across `evoke/**` and `scripts/**`. Imports followed into helper modules. Row = one draw expression
(multi-line calls grouped). All classifications cite `file:line` at the pin.

**Engine path:** `infer_post_distill.sh` -> `infer_batch.py` -> `infer_single.py` ->
`EvokePipeline` (`infer_single.py:766`) + `scheduling_evoke_diffusers.EvokeScheduler` (`:768`),
MODE=i2v + segment schedule, GEO on, `backward_zbuf`, vigeo, persistent decode, CFG off, no DMD,
pyramid `[1,1,1]`.

## 1. REACHABLE AFTER THE FORK — 7 sites (all INSTRUMENTED)

| id | file | function | ~line | API/draw | Generator | shape dep? | control-flow dep? | strict status | instrumentation |
|----|------|----------|-------|----------|-----------|------------|-------------------|---------------|-----------------|
| R1 | evoke/pipelines/pipeline_evoke.py | `prepare_latents` (called per chunk at :2791) | 371 | `randn_tensor([B,16,9,H/8,W/8])` per-chunk DiT input noise | main run generator (`infer_single.py:1434`, passed `:1485`) | yes (fixed shapes per config) | none — every chunk | INSTRUMENTED (active) | log draw order+shape per chunk; paired by seed |
| R2 | evoke/pipelines/pipeline_evoke.py | `prepare_video_latents` (warp first-frame encode; caller `_geo_encode_warp_to_latents:965`) | 424 | `vae.encode(first_frame).latent_dist.sample(generator)` | main generator | yes | fires every chunk (warp always rendered when not event) | INSTRUMENTED (active) | ledger entry; identical draw count both branches |
| R3 | evoke/pipelines/pipeline_evoke.py | `prepare_video_latents` (warp chunk encode; caller :965) | 432 | `vae.encode(chunk).latent_dist.sample(generator)` | main generator | yes | fires every chunk | INSTRUMENTED (active) | same |
| R4 | evoke/pipelines/pipeline_evoke.py | `_geo_encode_warp_to_latents` | 977 | `torch.rand(chunk_frames=9)` frame sigmas U[sigma_min=0, sigma_max=0.135] | main generator (`:975` unwraps list) | yes | none | INSTRUMENTED (active) | sigmas logged downstream by existing prints optional |
| R5 | evoke/pipelines/pipeline_evoke.py | `_geo_encode_warp_to_latents` — visibility-aware branch (ACTIVE: infer_batch passes `--visibility_aware_noise`, :437; cfg `infer_single.py:914`) | 996 | `randn_tensor(warp_latents.shape)` spatial-sigma noise | main generator | yes | branch selected by cfg flag (same both branches) | INSTRUMENTED (active) | uniform sibling :1003 dormant -> see D10 |
| R6 | evoke/pipelines/pipeline_evoke.py | `sample_block_noise` (stage-2 correlated renoise, invoked 2x/chunk at :1474 for pyramid stages i_s=1,2) | 573 | `torch.randn(block_number, block_size)` @ L@L.T | main generator (`generator[0]` unwrap) | yes (patch grid) | stage count fixed [1,1,1] | INSTRUMENTED (active) | note: `generator=None` fallback (:552-554) creates unseeded Generator — NEVER taken here (generator always passed); hazard documented |
| R7 | evoke/modules/geometric_state/da3_cloud.py | `_render_backward_multisrc_zbuf` covis point subsample (per source frame g in ids_all, M=2000) | 1486-1487 | `torch.randint(0, wp.shape[0], (M,), generator=_cgen)` | ISOLATED `_cgen = torch.Generator(device).manual_seed(EVOKE_WARP_SEED)` (:1474-1476); **global CUDA RNG if env unset** | yes (wp.shape[0], len(ids_all)) | len(ids_all) is schedule-determined (admission gates all default-off, da3_cloud.py:476-482) => aligned across branches | INSTRUMENTED **conditional on PRECOND-1: EVOKE_WARP_SEED must be exported** | upstream comment :1474 declares isolation intent; profile mandates the env var; unset => blocker |

Per-chunk main-generator draw sequence (post-fork), fixed order every chunk:
R2,R3 (VAE x2) -> R4,R5 (warp noise x2) -> [R7 isolated, does NOT touch main stream] ->
R1 (chunk noise) -> R6 x2 (stage renoise) -> DiT forwards (deterministic, dropout p=0, eval) ->
persistent decode (zero RNG, grep-verified).

## 2. PRE-FORK SETUP DRAWS — prefix-parity ledger (6 sites; execute once before chunk 0)

| id | file:line | API | note |
|----|-----------|-----|------|
| P1 | pipeline_evoke.py:388 (`prepare_image_latents`, called :2044) | `latent_dist.sample(generator)` reference-image latent | shared prefix artifact |
| P2 | pipeline_evoke.py:392 (:2044) | `latent_dist.sample(generator)` fake-video (33-repeat) tail latent | shared prefix artifact |
| P3 | pipeline_evoke.py:2060 | `torch.rand(1)` image sigma | `add_noise_to_image_latents` defaults True (:1747); infer_batch pins sigma range to [0,0] (:477) so the VALUE is 0 but THE DRAW STILL FIRES — must be counted for stream alignment |
| P4 | pipeline_evoke.py:2064 | `randn_tensor(image_latents.shape)` | same |
| P5 | pipeline_evoke.py:2068 | `torch.rand(1)` fake sigma | same |
| P6 | pipeline_evoke.py:2072 | `randn_tensor(fake_image_latents.shape)` | same |

## 3. EXPLICITLY DISABLED under strict profile — 10 sites (recipe-path flags forced/staying off)

| id | file:line | API | disabling condition | reason must stay off |
|----|-----------|-----|--------------------|----------------------|
| D1 | pipeline_evoke.py:1019 | `randn_like(latents_history_long)` in `_geo_maybe_noise_invisible_history` (:1007) | `invisible_history_noise=False` (argparse default; intentionally not passed — infer_batch.py:462-463) + second gate `video_latents is None` in i2v | history-corrupting RNG |
| D2 | pipeline_evoke.py:1023 | `randn_like(latents_history_mid)` | same double gate | same |
| D3 | pipeline_evoke.py:1100 (+ persistent `_geo_patchdrop_gen` creation :1092-1097 seeded from `args.seed`, wiring `infer_single.py:926`,`:1116-1117`) | `torch.rand(_Tn,_gh,_gw)` patch-drop Bernoulli | `geo_warp_patch_drop_ratio=0.0` (default; absent from shipped argv) | second long-lived RNG stream advancing across chunks |
| D4 | pipeline_evoke.py:2341 | `torch.rand(1)` short-tier per-rollout sigma lock (:2328-2329 reset) | `short_tier_noise_enabled=False` (default) | drains main generator at rollout start |
| D5 | pipeline_evoke.py:2708 | `torch.rand(1)` short-tier per-chunk sigma (closure :2700-2717) | same flag | variable per-chunk drain |
| D6 | pipeline_evoke.py:2710 | `randn_tensor(clean.shape)` tier corruption | same flag | same |
| D7 | evoke/utils/utils_base.py:909 | `randn_like(history_latents)` in `AdaptiveAntiDrifting.apply_frame_aware_corruption` | `use_adaptive_anti_drifting=False`; kwargs never passed by infer (grep clean); helper never constructed | DRIFT-TRIGGERED = data-dependent control flow adding RNG calls; worst case for pairing |
| D8 | pipeline_evoke.py:1333 | `randn_tensor(pred.shape)` DMD inter-step renoise | `use_dmd=False` (USE_DMD default '0', infer_batch.py:129; not in argv) | different timestep algebra + draws |
| D9 | pipeline_evoke.py:957 | `vae.encode(_padded).latent_dist.sample(generator)` warm-pad warp encode | `geo_warp_warm_encode=False` (default; absent argv) -> else-branch :964 taken | dormant sibling of R2/R3; if enabled changes draw shapes |
| D10 | pipeline_evoke.py:1003 | `randn_tensor(...)` uniform-frame-sigma warp noise | visibility-aware branch ACTIVE (R5) takes :996-997 | dormant sibling; same flag family, mutually exclusive branch |

## 4. UNREACHABLE under the strict recipe — with reason (complete hit list outside sections 1-3)

### 4a. Different engine / script (ODE pipeline and teacher runner never loaded)
| id | location | API | reason |
|----|----------|-----|--------|
| U01 | pipeline_evoke_ode.py:361 | `randn_tensor` prepare_latents | engine imports EvokePipeline (infer_single.py:766), never OdePipeline |
| U02 | pipeline_evoke_ode.py:474 | `torch.randn` sample_block_noise | same |
| U03 | pipeline_evoke_ode.py:587 | `randn_tensor` DMD renoise | same |
| U04 | pipeline_evoke_ode.py:1192+1196 | `torch.rand`+`randn_tensor` image noise | same |
| U05 | pipeline_evoke_ode.py:1200+1204 | fake-image noise pair | same |
| U06 | pipeline_evoke_ode.py:1223+1227 | video sigma+noise | same |
| U07 | pipeline_evoke_ode.py:1240+1247 | per-chunk frame sigmas+noise | same |
| U08 | pipeline_evoke_ode.py:378,382,414,422 | `latent_dist.sample` x4 | same |
| U09 | scripts/inference/infer_evoke_teacher.py:167-168 | Generator+`torch.randn` | separate launcher script, not invoked by infer_batch |

### 4b. Warp-cloud paths/gates not selected by shipped flags
| id | location | API | reason |
|----|----------|-----|--------|
| U10 | da3_cloud.py:721 (`ingest`, def :613) | `torch.randint(...,300000)` consist-ref downsample | `consist_gate=False` default (da3_cloud.py:476) |
| U11 | da3_cloud.py:1067 (`recall_frames`, def :1039) | `torch.randint` point subsample | recall hole-fill used by `_render_backward` only; zbuf path "accepts recall_* only for signature alignment" (:1452) |
| U12 | da3_cloud.py:1205 (`_render_multisrc`) | `torch.randint` covis | RENDER_MODE=backward_zbuf dispatches `_render_backward_multisrc_zbuf` (pipeline_evoke.py:816-819); unseeded global-RNG variant — must never be selected |
| U13 | da3_cloud.py:1336 (`_render_backward`) | `torch.randint` covis | same |
| U14 | da3_cloud.py:1857-1950 (`build_single_source_warp_mono`, chunk-0 ref warp) | — NONE — grep-verified RNG-free | positive result: `geo_chunk0_ref_warp` carries no random draw |

### 4c. Depth models not loaded (DEPTH_BACKEND=vigeo)
| id | location | API | reason |
|----|----------|-----|--------|
| U15 | third_party/da3/depth_anything_3/model/da3.py:169 | `torch.randint` quantile subsample | DA3 fallback backend not loaded |
| U16 | da3.py:431 | same | same |
| U17 | third_party/pi3/models/pi3x.py:322 | `torch.rand <= p_depth` mask | pi3 not loaded; train-aug context |
| U18 | pi3x.py:324 | `<= p_ray` | same |
| U19 | pi3x.py:326 | `<= p_pose` | same |

### 4d. Dropout / param-init / self-tests (eval mode or never executed)
| id | location | API | reason |
|----|----------|-----|--------|
| U20 | third_party/vigeo/vigeo/layers/drop_path.py:19 | `bernoulli_(keep_prob)` | early-return `drop_prob==0 or not training`; estimators run eval |
| U21 | third_party/pi3/models/dinov2/layers/drop_path.py:19 | same | same + pi3 not loaded |
| U22 | third_party/da3/.../dinov2/layers/drop_path.py:20 | same | same |
| U23 | evoke/modules/transformer_evoke.py:249 | `nn.Parameter(torch.randn...)` | weight-load init; deterministic given ckpt hash |
| U24 | transformer_evoke.py:908 | same | same |
| U25 | transformer_evoke.py:2593-2613 | `torch.randn/randint` self-test block | inside `if __name__ == "__main__"` (module import does not execute) |
| U26 | evoke/modules/evoke_kernels/triton_rope.py:163-311, manual_seed :289-309 | benchmarks/seeds | `__main__` only |
| U27 | evoke/modules/evoke_kernels/tiled_linear.py:352-355 | `manual_seed`+`randn` | `__main__` only |
| U28 | evoke/diffusers_version/transformer_evoke_diffusers.py:89 | param-init randn | class instantiated only outside engine (rope monkeypatch import executes no instance) |
| U29 | transformer_evoke_diffusers.py:422 | same | same |
| U30 | evoke/modules/evoke_teacher/dit_sparse_14b.py:452 | param-init randn | teacher model not loaded by post-distill engine |
| U31 | dit_sparse_14b.py:1359 | same | same |
| U32 | evoke/modules/student_sp.py:420-421 | seeded `Generator(cpu)+randn` SP-gradient selfcheck | SP diagnostics path; `sf_student_sp_ctx=None` single-GPU |
| U33 | third_party/da3/.../utils/ray_utils.py:164 | `torch.manual_seed(random_seed)` | app/export helper, not on inference path |
| U34 | ray_utils.py:251 | same | same |
| U35 | ray_utils.py:335 | same | same |
| U36 | third_party/pi3/models/dinov2/utils/utils.py:40-41 | `manual_seed` | hub/download util |
| U37 | schedulers: scheduling_evoke.py + diffusers_version/scheduling_evoke_diffusers.py (RUNTIME scheduler) | — ZERO RNG APIs (grep clean both) | positive result: scheduler.step/set_timesteps deterministic |

### 4e. Training-only modules (import graph excludes them from the engine)
| id | location(s) | APIs | reason |
|----|-------------|------|--------|
| U38 | evoke/dataset/online_materialize.py:87,93,98,160,176,183,827,875,954,1001,1019,1239,1330-1332,1389 | torch.rand/randn_tensor/latent_dist.sample/randint/random.uniform | training data materialization. Engine imports ONLY `_geo_resize_visibility_to_latent` (pipeline_evoke.py:989,1060) — verified PURE (index_select+adaptive_avg_pool3d+threshold+nearest interpolate, zero RNG) |
| U39 | evoke/utils/sf_warp_rollout.py:230,243,245 | `latent_dist.sample`, `torch.rand`, `randn_like` | imported only by utils_evoke_post (training) |
| U40-U44 | evoke/utils/utils_evoke_post.py:514-515,563,624,666,721,730,864,983,1248,1786,2054,2836,2872,2928,3036,3410-3412,3802,3819,4639,4690,4709,4908-4910,4926,5217,5266,5377,5394,5534,5542 | rand/randn/randn_like/latent_dist.sample/randint | RL/distillation training loop |
| U45-U49 | evoke/utils/utils_evoke_base.py:308,360,447,469,499,519,538,745,838,992 | torch.rand/randn_like/randn | training corruption + pyramid helpers (only :909 via AdaptiveAntiDrifting could be engine-adjacent -> disabled, see D7) |
| U50-U51 | evoke/utils/utils_recycle_batch.py:105-108,187,233 ; utils_recycle_single.py:88,119 | torch.rand/randint/random.* | training buffer recycle |
| U52-U54 | evoke/dataset/dataloader_dmd.py:71,92,192-193,209-210,229,383 ; dataloader_mp4_dist.py:304,559,590,628 ; dataloader_history_latents_dist.py:167-168,409,441,479 (+dataloader_multi_dataset.py:171) | random.seed/choice, torch.randint, Generator.manual_seed | DataLoader workers, training only |
| U55 | evoke/dataset/caption_operator.py:137, operators.py:139,156, data_config.py:18 | python `random` | training caption/augmentation ops |

## 5. Positive determinism findings (grep-verified zero-RNG components on the live path)

- Runtime scheduler (both variants): no draw APIs anywhere.
- Persistent VAE decode path (`_decode_chunk_persistent_cache` :438+, `_geo_persist_feat_map` :467-473/:516/:3044): zero RNG; mutable STATE only, pinned identical at fork by shared prefix.
- `_geo_even_threshold_map` Bayer dither (:1026-1047): deterministic ordered dither, no RNG.
- `_geo_resize_visibility_to_latent`: pure pooling/threshold.
- Text encoding incl. all `chunk_prompts` upfront (:2019-2022): no RNG.
- `build_single_source_warp_mono` chunk-0 warp: no RNG (see U14).
- CFG at guidance_scale=1.0: dead branch, verified zero forwards and zero draws (property :1700-1701).

## 6. COUNTS AND INVARIANT

Counting rule: row = one draw expression (grouped multiline = one row).

| population | count |
|------------|-------|
| REACHABLE_POST_FORK_RANDOM_SITE_COUNT (R) | **7** |
| ...of which INSTRUMENTED | **7** |
| ...of which EXPLICITLY_DISABLED while reachable | 0 |
| ...of which UNKNOWN | **0** |
| PRE-FORK prefix-parity sites | 6 |
| EXPLICITLY_DISABLED total (recipe-path flags off, incl. dormant siblings) | 10 |
| UNREACHABLE rows with stated reason | 55 |
| TOTAL inventoried rows | 78 |

**Invariant, meaningful form:** every site reachable after the fork is either ledger-instrumented or
explicitly disabled, with zero unknowns:
`R(7) == INSTRUMENTED_within_R(7) + DISABLED_within_R(0) + UNKNOWN_within_R(0)` -> **HOLDS**.

**Invariant, literal form as worded in the task** (`REACHABLE_POST_FORK == INSTRUMENTED_OR_DISABLED` over the
whole ledger, 7 vs 17): **FAILS trivially** because 10 disabled + 55 unreachable rows are not
reachable-by-construction; that reading is degenerate (it can only hold in a tree where nothing else
exists). Reported honestly rather than hidden; the coverage form above is the substantive claim and it
is the one SC1 needs.

## 7. Uncertainty (honest)

1. **PRECOND-1**: without `EVOKE_WARP_SEED` exported, R7 silently degrades to the global CUDA RNG
   (irreproducible warp-source selection; main-generator pairing unaffected since those draws bypass
   the explicit Generator). Profile mandates the export; verify in launch logs before G1.
2. **PRECOND-2**: no explicit `.eval()` found on the engine path; eval is inherited from
   `from_pretrained`. Cheap G1 assert required (all modules `.training == False`).
3. Estimator kernel nondeterminism (cuDNN reductions in vigeo) is outside any RNG ledger: cannot break
   draw alignment, but can perturb nominally identical pixels; measure same-seed rerun deltas at G1
   before publishing any byte-identical-prefix claim.
4. Line numbers valid at the pin only; re-run the battery if the pin moves.

---

## ADDENDUM (2026-08-25, post sealed review — inventory completeness fixes)

Rows missed by the original battery, classified during P7 dual review. REACHABLE counts unchanged.

| site_id | file | function/context | approx line | API | reachability under strict profile | reason |
|---|---|---|---|---|---|---|
| U12a | evoke/pipelines/pipeline_evoke.py | v2v add_noise_to_video_latents block (4 draw expressions) | 2105, 2109, 2122, 2129 | rand/randn_tensor | UNREACHABLE (MODE=i2v) | gated on `video_latents is not None` (:2103); i2v/segment path never supplies it |
| U12b | evoke/modules/geometric_state/da3_cloud.py | PersistentCloud.bound overflow resample | 290 | torch.randperm (global RNG, no generator) | UNREACHABLE (training-only) | sole constructor build_training_cloud_warp (:388); inference DA3FrameBank uses cloud_voxel=0.0 / no max_points (infer_single.py:284,:937); data-dependent trigger |

Battery-extension requirement for any future re-inventory: add patterns `randperm`, `np.random`, `random.` to the grep set. "UNKNOWN=0" claims are valid only relative to the extended battery.
