# GF0 Sealed Auditor Reports A/B/C (raw, 2026-08-24)

All pinned to AlayaLab/Evoke main tree `74d268516d95c8fceadd2378f91a73f9f187042b`.

---

## AUDITOR A — RNG/Diffusion (world-model-researcher, ses_fcb134dc9ffez8nQei7CzIPUmt)

Conclusion: EVOKE funnels ALL generation randomness through ONE CUDA torch.Generator seeded once per run from --seed; both schedulers are fully deterministic (zero scheduler entropy). Branch-coupled future noise achievable via Generator.get_state() snapshots; no capture hook exists; mid-rollout resume requires code changes.

Key verified facts:
- infer_single.py:1434 `generator = torch.Generator(device=device).manual_seed(int(args.seed))` (default 42); separate persistent gen for warp patch-drop (pipeline_evoke.py:1094–1097, seeded via :926,:1117).
- randn_tensor generator-honoring draws: pipe :371 (per-chunk init latents), :996/:1003 (warp vsnoise), :1333 (DMD per-step renoise), :2064–:2129 (conditioning), :2710; torch.randn :573 (stage2 block renoise); torch.rand :977,:2060,:2068,:2105,:2122,:2341,:2708; VAE latent_dist.sample(gen) :388–:432,:957.
- Global-RNG (NOT generator-seeded): randn_like :1019,:1023 (_geo_maybe_noise_invisible_history; flag default-off).
- Device: CUDA-resident generator (:775); replay must clone CUDA generator state.
- Scheduler step_euler/unipc deterministic; step_dmd renoises from caller-supplied tensor; generator params never read by schedulers.
- Draw cadence: one fresh latent draw per chunk (prepare_latents :2791→:371); under DMD fresh noise every denoising step except last (:1330–1337); stage2 adds block renoise (:1474–1485); strictly sequential order-dependent stream.
- SEED is run-level only. Coupling architecturally supported via get_state/set_state but rollouts are not resumable (geo_state/FrameBank/history internal to __call__); event_chunks machinery (infer_single.py:1441–1463) is a working mid-rollout divergence template.
- Minimal patch ≈10 lines: save generator.get_state() before :2791 (per chunk) and before :1333 (per DMD step); reuse via set_state().
- Hidden randomness: global-RNG randn_like :1019/:1023 (default off); unseeded fallback gen :554–556; --geo_chunk0_ref_warp DEFAULT-ON ViGeo forward — help text states chunk 0 "is no longer bit-reproducible"; no torch.use_deterministic_algorithms → nondeterministic GPU kernels make bitwise branch pixel equality unreliable; no inference dropout seen in audited files; no time-based seeds.
- Recommendation: implement capture at :2791/:1333 + in-call fork switch modeled on event_chunks; do NOT claim bitwise reproducibility — claim coupled-noise identity at logged tensors; empirically verify shared-prefix frames match under fixed seed.
- Call graph included in original report (main→pipe→prepare_latents/warp/patch-drop/stage2/scheduler).

## AUDITOR B — World-state fork (experimenter, ses_fcb0a01e7ffekSQOlUrUQHTCEf)

Structures: per-call geo_state dict (:583–594, init :2210) containing Pi3X FrameBank (frame_bank.py:11–17; entries frame[3,H,W] CPU fp32 quantized, c2w[4,4], chunk_idx, pixel_idx, optional cached_geometry; FIFO cap :40–44; note: no .retrieve caller in pinned pipeline — DA3-only inference, bank still written every chunk) and DA3FrameBank (da3_cloud.py:472, storage :601–606): pts{gid:(xyz,rgb)} GPU fp32, c2ws, frames{gid:(depth,intr,c2w,rgb)}, _pt_mask, side-state _probation/_carve_strike/colour-anchor stats/_win_hist(≤64)/counters/_pinned_wins. Scalars: source_image_pixel, prev_chunk_last_frame [1,3,H,W] (:3088), prev_chunk_last_decoded_latent [1,C,1,h,w] clone() :3125, da3_est, da3_K_pix, ~20 scalars (:672–712).

Mutation timeline: init pre-loop (:2245–2299); read during chunk (warp source :2567–2578; DA3 recall ≤ max_gid − lag·36); write post-denoise :3080–3130 (banks add at 36-stride gids :3110–3123, skipped for event chunks :3109); evict FrameBank FIFO, DA3 evict_before (da3_cloud.py:1019–1027) when hist_max_frames>0 or periodic re-anchor.

Deepcopy: LIKELY sufficient — all stored tensors freshly materialized (detach/cpu/quantize, boolean-mask indexing copies, explicit clones); NO views onto generation buffers; EXCEPTION geo_state["da3_est"] lazy model (da3_cloud.py:125,:142) must be SHARED not copied (GBs; stateless-per-call for 'da3'; ViGeo interleaved-stream safety UNVERIFIED despite reset_stream depth_backend.py:47–55).

Noncopyable resources: only da3_est. No locks/handles/lru_cache anywhere (grep). VAE feat cache _geo_persist_feat_map lives on PIPELINE not geo_state (:467–516).

Independent continuation: LIKELY yes with pipeline-attr caveat — shared-instance interference risks: _geo_persist_feat_map (written every chunk :516), _short_tier_rollout_sigma lock (:2329,:2340), transformer kv-cache (cleared per chunk :2996–2997, default off), process-global _GEO_DEPTH_ESTIMATORS (:57,:621–629). Scheduler reset per chunk (set_timesteps :2804); upstream batch-reuse comment supports sequential branch execution on one pipeline (infer_single.py:720–724).

Minimal fork serialization set: (1) real_history_latents rolling buffer (≥19 latents) + total_generated_latent_frames; (2) geo_state minus da3_est (both banks incl. side-state/counters, prev_chunk_last_frame, prev_chunk_last_decoded_latent, source_image_pixel, da3_K_pix, scalar cfg, v2v_chunk0_anchor_pix_idx, da3_is_i2v); (3) torch Generator states + camera cursor _geo_pose_k + event schedule/cursor (:2545,:3093); (4) conditional: anti-drift stats (:3000–3002), _short_tier_rollout_sigma, _geo_persist_feat_map. Items 3–4 LIKELY-required.

History accumulation: long/mid/short = (16,2,1) latents (defaults.py:14) + image-prefix latent + current 9-latent chunk (33px window, stride 36); banks grow unbounded unless CLI caps set (defaults 0, infer_single.py:432); DA3 recall lag da3_lag=1.

CPU unit test designs (paper): deepcopy storage independence via data_ptr checks; DA3 bank deepcopy excluding estimator sentinel test; two-clones independent continuation with mock step(); eviction determinism tests (FrameBank FIFO surviving indices; evict_before exact remaining gid sets across all five dicts).

## AUDITOR C — Protocol skeptic (novelty-red-team after 2 INFRA_FAILURE on reviewer, ses_fcaff89f9ffe5agIjpMCOl4hs9)

Core mechanism verified: single generator threaded through whole rollout (:1434, :1560); all draws consume it sequentially ⇒ "same seed ⇒ same future noise" holds ONLY IF identical draw counts in identical order.

O1 (VERIFIED, top threat): draw count/order is content- and flag-conditional. Event chunks skip warp render+encode entirely, substituting zeros (pipeline_evoke.py:2603–2616 vs :2616–2638) eliminating ≥2 draws per event chunk; _corrupt_clean_latent draws only when enabled+targeted (:2702–2710); adaptive anti-drift corruption triggered by MEASURED CONTENT DRIFT passes same generator (:2999–3011); visibility-aware vs uniform warp noise take different draw paths (:980–1005). Any intervention changing event placement/flags/drift status desynchronizes the shared stream — comparison then measures RNG divergence, not the intervention. Falsification test: instrumented dual-run logging every draw (call_idx, seed, state offset); same-seed runs differing only in event_chunks=[2] must show post-fork init-noise bitwise inequality (they will).

O2 (LIKELY, code VERIFIED): draws outside seeded generator — randn_like content-gated (:1013–1023); sample_block_noise generator=None fallback nondeterministic (:554–556).

O3 (VERIFIED as documented): bitwise reproducibility disclaimed upstream (--geo_chunk0_ref_warp default-ON help text: chunk 0 "no longer bit-reproducible"); triton/cuDNN kernel nondeterminism compounds. GF0 claims phrased as bitwise-equal PIXELS are dead; coupling asserted at pre-model tensor level (logged noise hashes) only. Test: two identical GPU invocations dump per-chunk latents via EVOKE_SAVE_DECODE_LATENTS hook, compare hashes.

O4 (VERIFIED structure / severity LIKELY): shared-instance leakage — _short_tier_rollout_sigma (:2698), _geo_persist_feat_map, _short_tier_print_count, module-global _GEO_DEPTH_ESTIMATORS (reset_stream discipline). Scheduler leakage REFUTED for sequential runs (set_timesteps → reset_scheduler_history, scheduling_evoke_diffusers.py). Test: branch A→B on one instance vs fresh instances; compare outputs.

O5 (UNVERIFIED, reasoning-only): observational confound — coupled-vs-uncoupled locality gain conflates coupling effect, intervention magnitude, drift rate, judge sensitivity; upstream docs admit warp feedback loops/drift-driven resets endemic.

Honest refutations: CFG cond/uncond draws NO randomness (:1257–1320) — prompt edits alone don't change RNG count; latent shapes prompt-independent (fixed H/W/latent_window_size); prompt_schedule swaps embeddings only (:2412–2418).

Conclusion: strict coupling as naively stated invalid on this codebase; survives only for twin branches byte-identical in flags/config consuming identical draw sequences up to fork, with coupling asserted on logged pre-model noise tensors, never pixels/seeds. Required: instrumented dual-run draw-log gate — equality up to fork, declared counted divergence after.
