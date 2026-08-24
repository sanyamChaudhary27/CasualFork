# Sealed Novelty Panel — 2026-08-24

Research question (identical for all panelists): Is CausalFork's proposed contribution (shared-prefix/noise-coupled counterfactual branching + deliberate mid-rollout intervention + minimal-change locality evaluation on an interactive video world model) already done, partially done, or open?

Constraints given identically to all: read-only; primary sources outrank project docs; resolvable identifiers; VERIFIED/LIKELY/UNVERIFIED/CONTRADICTED labels; no memory-citations; honest negative results; bounded length. No panelist saw another's findings before sealing.

## Seal ledger

| Seal # | Panelist / role | Mission | Agent type used | Attempts | Final session ID | Status |
|---|---|---|---|---|---|---|
| 1 | D — Counterfactual-literature hunter | find closer work than Twin Rollouts | general | 1 | ses_fcb68db28ffenCqCUZbhm7c6ef | SUCCESS |
| 2 | F — Wrapper prosecutor | strongest integration/demo case | novelty-red-team | 1 | ses_fcb689d71ffeuSyn2JH3C94GPW | SUCCESS |
| 3 | B — Twin-Rollouts auditor | primary-text audit of arXiv:2608.08982 | research-lead | 2 | ses_fcb5f9457ffeY3sn9sMjTk3m0N | SUCCESS |
| 4 | C — World-model capability auditor | implemented-vs-discussed capabilities | world-model-researcher | 2 | ses_fcb5ce6a9ffesVOB5u51rZDMN5 | SUCCESS |
| 5 | A — Prior-art hunter | closest prior work overall | general (type swapped after 2 infra failures) | 3 | ses_fcb583279ffeciqbLoro089lfv | SUCCESS |
| — | E — Data/benchmark auditor | What-If World / CG-World audit | causal-metrics-researcher → data-rl-researcher | 4 (ses_fcb617961ffe…, ses_fcb59f6f2ffe…, ses_fcb54a0eaffe…, ses_fcb52b800ffe…) | — | INFRA_FAILURE (zero evidential weight; benchmark question delegated to adjudicator) |

Failed intermediate sessions (all INFRA_FAILURE): B ses_fcb69178dffeipU465EGg0C09d; A ses_fcb61be21ffeO2kHBZzSAUrCXT; E ses_fcb5a0d14ffemp3HKZE7uxYrNZ; C ses_fcb5f5f4affeOph4zyHXkqDY6L.

---

## REPORT D — Counterfactual-Literature Hunter (general)

**Verification task (red-team citation)**

**arXiv:2604.20460 resolves to "CCTVBench: Contrastive Consistency Traffic VideoQA Benchmark for Multimodal LLMs"** (Zhou et al., submitted 22 Apr 2026) — a VideoQA *benchmark* using world-model-generated counterfactual counterpart videos plus contrastive-decoding inference. **VERIFIED, and it CONTRADICTS the red-team description**: there is no shared-prefix Cosmos-Predict-2 counterfactual synthesis method anywhere in this identifier. Any internal claim citing 2604.20460 for that purpose is a fabricated/misattributed citation and must be purged from project documents.

**Twin Rollouts status**

**arXiv:2608.08982 VERIFIED** (Ma, Shi, Xu; submitted 10 Aug 2026): "Twin Rollouts: Noise-Coupled Counterfactual Branching in Interactive Video World Models." It formalizes factual/CF branches sharing generated prefix + future exogenous noise, exact-by-construction abduction, a spatiotemporal locality metric against simulator ground truth, and CF-reward post-training. Critically, it is **a framework note whose experiments are explicitly "forthcoming"** — only a grid-world existence proof exists. Its novelty claim ("first formalization") is self-asserted, not peer-verified.

**Prior/close work found (all identifiers resolved by me via arXiv fetches unless noted)**

1. **How Can Driving World Models Do Counterfactual Prediction? — arXiv:2608.11601** (Zhang et al., 12 Aug 2026). VERIFIED. Formalizes abduction–action–prediction for driving world models; builds a controlled benchmark with factual + matched counterfactual outcomes; shows direct prediction fails; adds a training-free pipeline. **This is closer than Twin Rollouts on abduction + has experiments**, two days later.
2. **PersistWorld — arXiv:2603.25685** (Bardhan et al., ECCV 2026). VERIFIED via arXiv HTML + official site. RL post-training that branches K=16 continuations from a frozen self-generated prefix — but branches share *actions* and differ in *noise*: the stated dual of noise-coupled twin rollouts. Closest existing prefix-branching + reward-training precedent.
3. **CoCo — arXiv:2608.04653** (Shi et al., 5 Aug 2026). VERIFIED. Counterfactual-consistency training constraints (reference/inverse-action/zero-action rollouts) for action-controllable world models, with same-state multi-action counterfactual eval (Mini-SSMB). Action-intervention axis, experiments included.
4. **CWMDT — arXiv:2511.17481** (Shen et al., 21 Nov 2025). VERIFIED. Counterfactual world models via LLM-edited digital twins conditioning video diffusion; open-loop, editing/reasoning-based (approximate abduction), SOTA on two benchmarks. The pipeline Twin Rollouts positions itself against.
5. **CSVC — arXiv:2506.14404** (Spyrou et al.). VERIFIED via arXiv HTML. Prompt-steered black-box video-editing counterfactuals with causal-effectiveness/minimality metrics — the editing lineage CausalFork must be distinguished from.
6. **CounterScene — arXiv:2603.21104** (Jing et al.). VERIFIED via arXiv PDF. Structured counterfactual causal reasoning in closed-loop BEV driving world models for safety-critical generation.
7. **Counterfactual controllability framework — arXiv:2606.24152** (Wang et al., Jun 2026). LIKELY (resolved via search excerpts of the arXiv page, not fetched directly); position paper, no method/training procedure.
8. Bear et al., Unifying Vision via Counterfactual World Modeling, arXiv:2306.01828 — VERIFIED via official repo; earlier masked-predictor lineage, not generative branching.
9. Solvane, "CWM: Intervention Consistency" preprint (polaris02310.github.io, Nov 2025) — non-archival personal-site PDF with partially garbled references; treat as UNVERIFIED quality, not citable evidence.

**Unresolved:** "What-If World" (contrastive intervention-following benchmark cited in Twin Rollouts' positioning) — I could not independently resolve an identifier; UNVERIFIED.

**Negative result**

Across query classes — (a) action interventions in interactive WMs, (b) state/mechanism interventions, (c) shared-prefix/noise-coupled branch pairs, (d) abduction-style video counterfactuals, (e) locality/minimal-change metrics vs simulator GT, (f) reward/post-training on factual–CF pairs, (g) Genie-style branching evaluation — **I found no published work implementing noise-coupled mid-rollout branch pairs with per-sample verifiable locality in a full interactive video world model.** Nothing closer than Twin Rollouts on that specific combination. However, each ingredient exists separately (11601's abduction benchmark, 25685's prefix branching + contrastive rewards, 463's consistency constraints, 14404's minimality metrics).

**Implication**

CausalFork cannot claim the general idea of counterfactual branching or CF-reward post-training as novel; the defensible novelty window is narrow (exact noise coupling + per-sample locality verification inside one interactive WM system, executed end-to-end). Twin Rollouts being experiment-free means first *executed demonstration* is still open — but 2608.11601 already occupies "controlled CF benchmark with ground truth." Any CLAIMS.md entry must cite 2608.08982, 2608.11601, 2603.25685, 2511.17481, and 2506.14404.

---

## REPORT F — Wrapper Prosecutor (novelty-red-team)

## Conclusion
As specified today, CausalFork is an integration/demo layer. Every load-bearing component exists in primary sources I resolved myself: branching-with-intervention is a shipped interaction pattern (Genie 3 "promptable world events," DeepMind blog, Aug 5 2025 — VERIFIED); counterfactual video generation via conditioning edits exists (CWMDT, arXiv:2511.17481 — VERIFIED); paired counterfactual evaluation with simulator ground truth exists since 2020 (CoPhy, arXiv:1909.12000, ICLR'20 — VERIFIED); the *exact* formalization in SPEC §2–§3 (shared prefix + shared future noise + descendant-mask locality metric) was published three weeks ago (Twin Rollouts, arXiv:2608.08982 — VERIFIED; CLAIMS.md C006 correctly flags this). Open action-conditioned backends are commodity (etched-ai/open-oasis 500M weights — VERIFIED; microsoft/mineworld — VERIFIED). What remains genuinely unclaimed: **an empirical instantiation** — noise/prefix-coupled twin branches on a real pretrained interactive video world model, with measured locality against naive-editing controls. Twin Rollouts states "experiments are forthcoming"; its Figure 1 is a deterministic grid world. Nobody has done this on a public video-world-model checkpoint.

## Closest prior art
1. **Twin Rollouts (arXiv:2608.08982)** — formalization, locality metric, verifiable rewards; experiments deferred. Kills any "we formalize branching" claim.
2. **Genie 3 blog** — shipped mid-rollout text interventions ("altering weather… introducing objects"), explicitly marketed as "what if" scenarios; closed preview, no paired branches, no locality measurement.
3. **CWMDT (arXiv:2511.17481)** — LLM-edited digital-twin text conditions a video diffusion model to generate counterfactuals; open-loop, single-shot.
4. **CoPhy (ICLR'20)** — paired do-intervention dynamics with ground-truth alternative outcomes; synthetic, non-interactive.
5. **2026 eval field** — Omni-WorldBench (arXiv:2603.22212, affected/unaffected-entity causal scoring ≈ proto-locality), WBench (arXiv:2605.25874, event-editing turns), CRONOS (May 2026, intervention-based counterfactual consistency in Unreal), WorldExam (arXiv:2608.02603), YoCausal (arXiv:2605.30346). The "benchmark" lane is crowded — VERIFIED via fetched abstracts.

## Strongest novelty objection
Every element is prior art; only the composition is new, and composition is engineering. SPEC §7 Phase A–C is prompt/schedule parameter search around existing samplers — indistinguishable from prompt tuning. §3's reward vector re-weights standard metrics (LPIPS/CLIP/VLM-judge) that Omni-WorldBench-style suites already combine. Without noise coupling, "minimal change" degenerates to masked regeneration/video inpainting, which is decades old. Misleading wording a critic would strike: "first counterfactual branching" (Twin Rollouts owns it), "causal" without coupling (SPEC §2 honestly concedes this — keep that concession), "RealityBench/CausalPairs" presented as novel benchmarks without citing the five suites above.

## What would survive criticism
(1) First demonstration of the published twin-rollout construction on a released pretrained interactive video world model, since Twin Rollouts explicitly defers scale-up. (2) A controlled negative result quantifying that naive prompt-edits at t* cause global drift (coupling-off control), versus coupled branches — converting the demo into measurement science. (3) Tier-C mechanism interventions appear in *none* of the fetched literature for generative video worlds (CRONOS varies appearance/viewpoint only) — but too risky for 48h.

## Required experiment (48h, falsifiable)
Pick ONE open backend (open-oasis verified available; MineWorld preferred if checkpoints restored). Implement `fork(state,t*)` by replaying the stored prefix context window; run paired futures under identical action/camera streams: (a) uncoupled-seed naive prompt edit; (b) coupled sampling variates where the backend permits (feasibility currently UNVERIFIED — inspect code first); (c) coupled + best-of-N schedule search scored by predeclared R_locality/R_intervention. ≥10 scenes × ≥3 interventions, simulator-derived changed/invariant masks, predeclared gate: median out-of-mask divergence(b,c) < (a) with coupling-off ablation reproducing stochasticity levels. Ship notebook + artifacts + negative controls. This instantiates the one gap no fetched source fills.

## Blockers
None fundamental. Risks: per-backend noise coupling may be impossible (then honestly label "prefix-shared/seed-matched" and gate on search-vs-naive instead); MineWorld checkpoint availability post-takedown UNVERIFIED; GPU-hours for N-scene sweep must fit Colab limits.

*Negative results declared: I found no shipped synchronized-A/B branch product, no published empirical twin-rollout on a video world model, and no prior best-of-N-over-intervention-schedules work — searched; absence, not proof.*

---

## REPORT B — Twin-Rollouts Auditor (research-lead)

## Conclusion

arXiv:2608.08982v1 is real and confirmed: **"Twin Rollouts: Noise-Coupled Counterfactual Branching in Interactive Video World Models"**, Yu Ma, Hongli Shi, Xinran Xu, submitted **10 Aug 2026** (v1 only, 49 KB source, cs.LG). It is a framework/positioning **note**: formal definitions plus one small deterministic grid-world existence proof. The internal unverified note is **CONFIRMED** — full video-scale, data-engine, and post-training experiments are explicitly deferred to "the next revision," and Section 3 contains only the grid-world existence proof.

## Evidence

All items below read directly from the arXiv abstract page and LaTeXML HTML full text (v1) today; section references given.

**Identity** — VERIFIED: title, authors, `[v1] Mon, 10 Aug 2026`, license "arXiv.org non-exclusive-distrib 1.0". No code/data link appears on either page.

**1. Formal claims vs demonstrated experiments** — VERIFIED: §2 gives Definitions 1–3 (explicit-noise rollout; intervention `do(a_{t*}:=a′)` or `do(x_{t*}:=x′)`; locality/outcome-fidelity metrics and reward `R = −(λ_O·O + λ_L·L)`) plus remarks on exact abduction and metric operationalization. The only demonstrated artifact is Figure 1 (§3): qualitative — "the region outside D_t is nearly silent" with coupling on; "lights up" with coupling off. No tables, numbers, baselines, seeds, or model/training details appear anywhere in the text I read. The abstract self-describes: "establishes the formal framework… experiments are forthcoming."

**2. Full experiments vs existence proofs** — VERIFIED: §3 calls itself "an existence proof"; §5: "not evidence of scale." Even the grid-world twin branches come from "a trained autoregressive world model," but with zero experimental detail. There are **no full experiments**.

**3. Deferred/forthcoming** — VERIFIED: Abstract: "experiments are forthcoming." §3: "Scale-up to a full interactive video world model, together with the data engine and post-training results, is deferred to the next revision."

**4. Intervention types** — VERIFIED (Def. 2): action edits and state edits at t*. §5 adds the operative constraint: under egocentric viewpoint-moving interventions the locality term L becomes vacuous, so training signal is confined to **viewpoint-preserving interventions** "until camera-compensated comparison is validated."

**5. Reward definitions** — VERIFIED (Def. 3): L penalizes divergence outside descendant masks D_t; O measures fidelity inside D_t against simulator ground-truth re-renders from a forked state; R is their weighted negative sum, "computable without a learned judge." Remark (operationalization): D_t from per-pixel difference channel (+ entity channel where available); empty-complement frames make L **undefined, not zero**; overlay masking + magnitude thresholds absorb renderer noise. Crucially, this reward is **defined, not validated**: no result shows it correlates with quality or improves post-training — LIKELY material to our "search before RL" gate.

**6. Stated limitations** — VERIFIED (§5): simulator-dependence of masks; viewpoint-intervention vacuity (mitigated by per-class stratification); renderer nondeterminism handled by masking/thresholds "rather than assumed away"; existence-proof-only scale evidence.

**Novelty claims** — REPORTED, not verified by me: hedged "to our knowledge first" statements for (C1) generation-time branching formalization, (C2) per-sample verifiable locality, (C3) first factual–counterfactual-pair verifiable reward. §4 positions against seven works (CWMDT, What-If World, CSVC/image-domain diffusion, PersistWorld, counterfactual-controllability framework, CounterScene, RLVR-for-world-models). I did not independently audit those cited papers.

**Relevance flag**: the formal construction (shared prefix, shared future exogenous noise, minimal-change locality, simulator-forked ground truth as verifiable reward) substantially overlaps CausalFork's stated research invariants, now publicly dated 10 Aug 2026.

## Uncertainty

- HTML is a LaTeXML conversion; I did not diff against the PDF (page said build-log support note). Content agreement LIKELY exact but UNVERIFIED byte-for-byte.
- Figure 1 judged from caption/text only, not visual inspection.
- Author novelty claims unchecked against the seven cited works.
- No v2 exists as of today; a "next revision" may appear and change everything above.
- I did not search GitHub/HF for unofficial code; absence of links on arXiv pages establishes only that arXiv lists none.

## Recommendation

Update `CLAIMS.md`: record this paper as published prior art (v1, 10 Aug 2026) covering the formal branching/locality/reward design space; strip any implied CausalFork novelty from formalism alone and re-anchor our contribution claim on executed, measured experiments (G-gates) and the hero demo. Monitor for v2 before any dependency decision; there is currently no code/weights surface to audit.

## Blockers

None. Paper fully accessible; review complete.

---

## REPORT C — World-Model Capability Audit (world-model-researcher)

**Conclusion:** EVOKE's verification claim is CONFIRMED: scheduled per-chunk prompt/event changes during an ongoing rollout are implemented in released code, with a camera-indexed external world state bank anchoring scene structure. Across every open interactive world model audited, however, **branching from a shared prefix, cross-branch noise coupling, editable world state, and exact session replay are implemented nowhere** — CausalFork's core contribution remains unoccupied territory.

**Evidence**

**EVOKE** (arXiv 2608.13546; github.com/AlayaLab/Evoke, Apache-2.0; HF AlayaLab/Evoke weights, apache-2.0):
1. *Mid-rollout intervention* — **VERIFIED**: `MODE=segment` launcher consumes `schedule_*.json`; README demos switch prompts at chunk 3 of 6 ("the sky ignites"); paper: "per-chunk conditioning enables prompt changes and event control throughout the sequence." Switch granularity is chunk boundaries (1.5 s), not intra-chunk.
2. *Branching* — **NOT IMPLEMENTED** (no fork API in repo/docs).
3. *Stochastic control* — **VERIFIED (run-level)**: `SEED` is a documented launcher knob. Cross-branch noise coupling at a fork point: not exposed.
4. *Persistent state* — **VERIFIED (persistent, not editable)**: point-cloud bank with write/read/evict, addressed by camera pose. No documented edit/delete-object operation. Caveat: `GEO_HIST_MAX_FRAMES` eviction changes what warp sees — a recipe change that breaks comparability.
5. *Replay* — **PARTIAL**: `run_info.json` records recipe/checkpoint; finished cases skip on rerun; v2v mode re-seeds rollouts from reference video+poses (pixel-level prefix replay). Latent/session-state save-load: not implemented.

Hidden caveats that prevent wasted GPU hours: distilled checkpoints were trained **v2v-only** (`geo_condition_{i2v,t2v}_ratio: 0.0`) so i2v/t2v are zero-shot (confirms CLAIMS.md C004); `diffusers` is pinned to a **dev fork not on PyPI**; required depth backend **ViGeo is CC-BY-NC-4.0** — non-commercial despite the Apache repo; 14B model, reported 384×640@24fps, 2.11 s/chunk on H200; teacher sampling needs ~56 GB bf16.

**Yume 1.5** (stdstu12/YUME, Apache-2.0; Yume-5B-720P weights, Dec 2025; arXiv 2512.22096, CVPR 2026): keyboard/mouse control plus paper-claimed "text-based event editing" — **LIKELY** as capability, but mid-rollout event-switching implementation status **UNVERIFIED by me** (paper says Event Description is encoded "only during the initial generation phase"). Claim C005 stands as UPSTREAM_REPORTED. Reported 12 fps @540p on A100. No branching/state/replay APIs found.

**Matrix-Game 2.0** (SkyworkAI/Matrix-Game, MIT code+weights, 1.8B): real-time streaming keyboard/mouse control, but the **text branch was removed entirely** — semantic interventions are architecturally impossible. Key negative result.

**Matrix-Game 3.0** (Mar 2026, arXiv 2604.08995, MIT): 5B (and 28B) with camera-aware long-horizon memory, `--prompt` and `--seed` flags (**seed control VERIFIED** in released command). Mid-rollout prompt switching: **UNVERIFIED**. "40 FPS" requires **8 GPUs for DiT + 1 GPU for VAE decode** — headline number is a cluster figure.

**Oasis** (etched-ai/open-oasis, MIT, 500M weights): action-conditioned frames only; larger models closed/API (Oasis 3). No branching/state/replay.

**Genie 3 / closed frontier systems**: no public checkpoints or inference path; any capability claim about them is **UNVERIFIED** and unusable for our purposes.

**Uncertainty:** I verified EVOKE via official README/HF card/arXiv HTML, not by executing code; segment-mode output quality is demonstrated by curated GIFs, not controlled metrics. Whether Yume 1.5's released code supports mid-rollout event switching needs a repo-level check. MineWorld, WHAM, LingBot-World, AlayaWorld, HY-World surveyed only via secondary mentions here; Twin Rollouts (arXiv:2608.08982) not independently audited in this pass.

**Recommendation:** Treat EVOKE as primary backend candidate: it uniquely offers (a) implemented per-chunk prompt schedules, (b) exposed seeds, (c) an explicit, serializable external state bank whose cloning is a plausible fork mechanism (untested hypothesis — flag as such). Implement `fork()` as bank-deepcopy + shared prefix latents + same seed, and label comparisons honestly since coupled noise beyond chunk 0 is unverifiable. Matrix-Game 2.0 is unsuitable (no text). Verify Yume 1.5's event-editing code before relying on it.

**Blockers:** None absolute. Two constraints: ViGeo CC-BY-NC-4.0 blocks commercial use of EVOKE's shipped pipeline; EVOKE's dev-fork diffusers pin complicates environment setup.

---

## REPORT A — Prior-Art Hunter (general)

**Verification task first.** I fetched `arxiv.org/abs/2604.20460` directly. It resolves to **CCTVBench** ("Contrastive Consistency Traffic VideoQA Benchmark for Multimodal LLMs," Zhou et al., submitted 2026-04-22) — a VideoQA benchmark pairing real accident clips with world-model-generated counterfactual counterparts. **VERIFIED**: the internal red-team's description ("shared-prefix counterfactual synthesis on Cosmos Predict-2") is **INVALID** for this identifier. Separate searches ("Cosmos Predict 2 counterfactual branch shared prefix seed-matched rollout NVIDIA") found no such paper anywhere; cosmos-predict2's own README lists its paper as "coming soon" (**VERIFIED** via github.com/nvidia-cosmos/cosmos-predict2). Treat any claim resting on that citation as unsupported.

## New prior art beyond RESEARCH.md, ranked by closeness to the full combination

1. **"How Can Driving World Models Do Counterfactual Prediction?"** — arXiv:2608.11601 (Aug 2026). **VERIFIED** (abs fetched). Formalizes the abduction–action–prediction gap; builds a controlled CARLA benchmark with factual and *matched* counterfactual outcomes; empirically shows direct action-conditioned prediction fails to preserve the realized world; offers a training-free pipeline. Closest verified match to CausalFork's "same world + one changed factor vs simulator ground truth," though driving-only, non-interactive, no noise coupling or camera-trajectory sharing.
2. **CWMDT** — arXiv:2511.17481 (Nov 2025). **VERIFIED** (abs fetched). First formalization of counterfactual world models taking interventions as explicit inputs; LLM-reasoned digital twins condition a video diffusion model; SOTA on RVEBench/FiVE. Overlaps the "intervention-conditioned counterfactual video" core, but is editing-based (no shared prefix), offline, non-interactive.
3. **Genie 3 "promptable world events"** — DeepMind blog. **VERIFIED** (official blog). Mid-rollout text events alter weather/spawn objects in a real-time interactive world model, explicitly framed as enabling "what if" scenarios. Closed-source, no branch pairs, no locality evaluation — but it publicly owns the "mid-rollout intervention in an interactive WM" component.
4. **SL-FM** — arXiv:2607.10206 (Jul 2026). **VERIFIED** (abs fetched). Source-intervenable flow-matching policies with *matched-prefix* counterfactual interventions (shared seed/prefix/stochastic draws); changes routes in 91.1% of matched-prefix tests. Non-video (imitation policy), but implements exactly the shared-prefix + controlled-divergence protocol.
5. **CounterScene** — arXiv:2603.21104 (Mar 2026). **VERIFIED** (abs fetched). Minimal targeted interventions on a causally critical agent in generative BEV world models (nuScenes); measures adversarial effectiveness with trajectory realism. Driving/BEV only.
6. **Autonomous Video Generation with Counterfactual Controllability** — arXiv:2606.24152 (Jun 2026). **VERIFIED** (abs fetched). Position/framework paper (Tsinghua): intervention-conditioned futures, branch verification under shift, distillation. No working system of CausalFork's type; competes for framing vocabulary ("counterfactual controllability").
7. **CCTVBench** — arXiv:2604.20460. **VERIFIED** (see above). Benchmark built on minimally-different real/generated counterfactual video quadruples — precedent for paired-counterfactual evaluation, not generation.
8. **IC-World** — arXiv:2512.02793 (ECCV 2026; code at github.com/wufan-cse/IC-World, **VERIFIED** via official repo). Multi-video generation of one consistent world with GRPO-trained geometry/motion-consistency rewards — a direct precedent for reward-based consistency training across parallel rollouts. Related: **ShareVerse**, arXiv:2603.02697 (**VERIFIED** abs).

## Negative results (query classes used)

- "shared-prefix/noise-coupled branching in interactive video world models": only the already-listed Twin Rollouts note (2608.08982) surfaced; no independent replication found.
- "open interactive image-to-video WM with A/B branch pairs, identical prefix, same future camera": none found among Yume/EVOKE/Matrix-Game/Hunyuan-GameCraft/minWM/PAN/Astra listings in two awesome-lists.
- "Cosmos Predict-2 counterfactual branching": no primary source exists.

## Bottom line

No verified source implements the full four-part combination. However, the formal/eval story has close neighbors (2608.11601, CWMDT) and mid-rollout intervention is publicly demonstrated (Genie 3). Novelty should be staked narrowly: noise/state-coupled twin branches inside an open interactive image-to-video world model with locality rewards and search — with explicit deltas versus 2608.11601 and CWMDT written into CLAIMS.md.
