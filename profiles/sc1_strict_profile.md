# SC1 Strict Profile — Human Explanation (P1)

**Pin:** AlayaLab/Evoke @ `74d268516d95c8fceadd2378f91a73f9f187042b` (read-only clone verified, clean tree).
**Scope:** twin branches inside the EVOKE post-distill recipe, engine `MODE=i2v` + segment schedule,
`GUIDANCE_SCALE=1.0`, pyramid 3x1 steps, persistent VAE decode, `backward_zbuf` cloud warp, vigeo depth.
Machine-readable counterpart: `profiles/sc1_strict_profile.json`. Full RNG ledger: `profiles/sc1_stochastic_site_inventory.md`.

## Fork semantics

- A **VAE valid window** covers 33 pixel frames = 9 latent frames (`latent_window_size=9`, VAE
  temporal stride 4). The **rollout/prompt chunk stride** is 36 pixel frames. Window and stride are
  **distinct quantities** - a chunk is identified by its stride position, never by the window size.
- The fork sits at a **chunk boundary `c*`** (first post-prefix chunk). Fork identity is always
  **chunk-index based**, never pixel-frame based. Chunks `0..c*-1` are generated
  identically in both branches and frozen as the **shared prefix artifact** (decoded pixels plus the
  pipeline state that crosses the boundary: FrameBank store, persistent-VAE feature cache).
- The **only** divergence is the prompt: the CF branch passes `chunk_prompts` entries with keys >= c*
  through the segment-mode schedule JSON. In the engine this swaps `prompt_embeds` per chunk
  (`pipeline_evoke.py:2019-2022` encode-upfront; `:2413-2416` select-per-chunk). It is explicitly
  text-embedding-only: "warp / camera / frame bank stay on the baseline path" (`:2411-2412`).
- `event_chunks` MUST be empty in both branches. Upstream itself documents that an empty set leaves
  the rollout "byte-for-byte identical to baseline" (`:1814-1815`, `:2404-2410`) — which is exactly why
  it must not be the intervention mechanism: it changes camera cursor and warp availability, i.e. far
  more than the text condition.

## Why byte-identical config matters: the pairing invariant

Every stochastic site on the recipe path draws from **one explicit generator**
(`torch.Generator(device=device).manual_seed(seed)`, `infer_single.py:1434`) threaded through
`pipe(**kwargs)` (`:1485`). If both branches run byte-identical configs with the same seed, then at
every post-fork step k each branch consumes an **identical sequence of draw shapes** from its
generator — only the prompt embedding differs. That converts A/B comparison from "two samples" into a
**paired-draw comparison**, which is the evidentiary core of SC1.

**Operational definition of byte-identical:** SHA256 over canonical JSON of {all recipe env exports} x
{resolved argv incl. --seed} x {jsonl row minus [prompt, prompt_schedule]} x {EVOKE_WARP_SEED} x
{checkpoint hashes}. Only prompt fields are excluded. Anything else differing = invalid pairing.

## Classification rationale

### SAFE — deterministic or provably identical under byte-identical config
Examples: `NUM_INFERENCE_STEPS=3` (ignored under the pyramid), `NOISE_CENTER=0`,
`WARP_MODE=fixed_mem`, resolution/FPS, presentation-only hooks (segment dumps, HUD burn-in — all
downstream of every RNG site), `ZBUF_DESPECKLE=0` (upstream documents the off-path as "byte-identical
to the original", `da3_cloud.py:1458`).

Special case — **CFG off**: `do_classifier_free_guidance` is literally `_guidance_scale > 1.0`
(`pipeline_evoke.py:1700-1701`). At 1.0 the uncond forward block (`:1281-1320`) never executes:
verified zero extra forward passes AND zero RNG draws. (CFG never draws anyway, but at 1.0 even the
compute disappears.)

### DISABLE_FOR_SC1 — must stay forced-off; content/data-dependent control flow that can add or remove RNG calls
These are default-off in the shipped argv and must remain so:

| Option | Why disabled |
|---|---|
| `use_adaptive_anti_drifting` | corruption fires **only when a drift detector trips** (`:2999-3010`) -> randn_like (`utils_base.py:909`). Data-dependent RNG insertion = worst case for pairing. Helper is never constructed today (no kwargs passed). |
| `short_tier_noise_enabled` (+ `sigma_lock_per_rollout`) | drains the main generator once at rollout start (`:2340-2342`) plus per-tier per chunk (`:2708,:2710`) — variable draw counts. |
| `geo_warp_patch_drop_ratio > 0` | creates a **second long-lived generator** `_geo_patchdrop_gen` seeded from args.seed (`:1092-1100`, seed wiring `infer_single.py:926,1116-1117`) advancing across chunks. Deterministic alone, but adds an independent stream and a content-conditioned mask surface. |
| `geo_warp_vis_cap > 0` | keep_frac is measured per frame from visibility (`:1076-1085`): data-dependent conditioning change (the Bayer dither itself is RNG-free). |
| `invisible_history_noise` | randn_like on history tiers (`:1019,:1023`); double-gated by flag AND `video_latents is None`. Deliberately not passed upstream too (`infer_batch.py:462-463`). |
| `use_dmd` | different timestep algebra + renoise draw (`:1330-1337`). |
| `restrict_self_attn`/`use_kv_cache` pair | hidden mutable cross-step cache state; `RESTRICT=0` keeps both off. Re-enable only after proving cache-state parity across branches. |

Also forced-off by policy: `GEO_HIST_MAX_FRAMES` unset (changes point-cloud bounds -> changes bank
store sizes -> changes covis draw counts).

### INSTRUMENT — allowed on, ledger-instrumented (see inventory for the full draw ledger)
- The seven reachable post-fork sites (per-chunk DiT noise, two warp-VAE encodes, warp frame sigmas,
  visibility-aware warp noise, 2x stage-2 correlated renoise, zbuf covis subsample).
- Config carriers of those draws: pyramid settings, warp sigma parameters +
  `visibility_aware_noise=true` (active spatial-sigma branch `:980-997`; uniform fallback `:998-1005`
  dormant), `RENDER_MODE=backward_zbuf`, `DEPTH_BACKEND=vigeo`, `VAE_DECODE_TYPE=persistent`, SEED.
- `geo_chunk0_ref_warp` (default-on): the brief's worry ("non-reproducible") was **not confirmed at
  the RNG level** — its render path `build_single_source_warp_mono` (`da3_cloud.py:1857-1950`)
  contains zero random APIs (grep-verified). It renders deterministically from the shared reference
  image, hence identical across branches. Residual risk shifts to estimator kernel determinism, a G1
  empirical check, not an RNG-ledger item.
- Persistent mutable attributes (`_geo_persist_feat_map :467-473/:516/:3044`,
  `_short_tier_rollout_sigma/_short_tier_print_count :2328-2329` reset per rollout,
  `_GEO_DEPTH_ESTIMATORS :58/:621-629`, `vae._feat_map`/`clear_cache`): these are **state, not RNG**.
  Their evolution is deterministic given identical latents, and the shared prefix pins them identical
  at the fork boundary. They belong in the state ledger because any asymmetric reset would silently
  desynchronize downstream draws.
- Eval-mode enforcement: no explicit `.eval()` exists on the engine path (grep); diffusers
  `from_pretrained` defaults to eval and DiT dropout is p=0.0, but third_party DropPath gates on
  `.training`. PRECOND-2 makes the assertion a cheap mandatory G1 check.

## Fallback consequences

If PRECOND-1 fails (EVOKE_WARP_SEED unset), the covis subsample falls into the global CUDA RNG
(`da3_cloud.py:1476 _cgen=None`). Two consequences, honestly separated:
1. Run-to-run irreproducibility of warp source selection (violates the reproducibility contract);
2. NOT a desync of the main generator stream — those draws bypass the explicit Generator object, so
   paired noise draws remain aligned. The damage is confined to warp-source selection variance.

If any instrumented site is later found un-instrumented, or PRECOND-2 fails: strict pairing is void;
SC1 evidence downgrades from "paired strict" to "unpaired observational", and preservation claims must
then lean on simulator ground truth or human review instead of RNG pairing.

## Honest limits

- UNKNOWN_BLOCKER count is **0 statically**, conditional on PRECOND-1/PRECOND-2. If either cannot be
  guaranteed pre-launch, the profile says so loudly and strict mode is invalid.
- Estimator kernel nondeterminism (cuDNN/cuBLAS reduction order in vigeo/DA3 inference) is out of scope
  of the RNG ledger; it cannot break draw alignment but can make nominally-identical pixels differ.
  G1 should measure same-seed rerun deltas before any "byte-identical prefix" claim is published.
- All line numbers cite the pinned commit; re-run the grep battery if the pin moves.
