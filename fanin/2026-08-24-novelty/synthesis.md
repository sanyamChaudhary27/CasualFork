# Synthesis Report — Sealed Novelty Panel, 2026-08-24

Session: ses_fcb4eab7affeZgjlSZyIXshprY (general) · Status SUCCESS · Revealed reports: A,B,C,D,F simultaneously after sealing; E INFRA_FAILURE excluded.

**PROCESS DEFECT (recorded by adjudicator):** this document was not persisted to disk before STAGE 5 dispatch; the adjudicator received no synthesis text and therefore adjudicated directly against primary sources and the verification list V1–V7. Conclusion-blindness was preserved (strictly exceeded), but the STAGE 3→5 handoff deviated from COMPANY.md protocol. Orchestrator error.

---

# SYNTHESIS — Sealed Novelty Panel, 2026-08-24

**Panel integrity:** 5/6 reports usable; E (benchmarks) INFRA_FAILURE — zero evidential weight; What-If World / CG-World remain OPEN questions, not evidence. Seal order per ledger: D→F→B→C→A.

## 1. Novelty-overlap matrix

Legend: **ID** identical · **SO** strong overlap · **PO** partial overlap · **AO** apparently open · **?** unknown

| Component (SPEC.md) | TwinRollouts 2608.08982 | DriveCF 2608.11601 | CWMDT 2511.17481 | PersistWorld 2603.25685 | Genie 3 | EVOKE | IC-World 2512.02793 | SL-FM 2607.10206 | CCTVBench 2604.20460 | WhatIfWorld | CG-World |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Branch protocol / noise coupling | **ID** (formalized, unexecuted) | PO (abduction, no coupling) | AO (open-loop editing) | **SO** ("stated dual": shares actions, varies noise) | AO (no branch pairs) | AO (fork API absent — C) | PO (parallel same-world videos) | **SO** (matched-prefix, non-video) | PO (paired eval data) | ? | ? |
| Mid-rollout intervention layer | SO (Def. 2, formal only) | PO (action edits, driving) | PO (edit-conditioned, single-shot) | PO (noise-only variation) | **ID** (shipped, closed, blog-verified) | **ID** (implemented `MODE=segment`, chunk-granularity) | AO | PO (policy source edits) | AO | ? | ? |
| Minimal-change locality eval | **ID** (descendant-mask metric + sim GT; *defined, not validated* — B) | **SO** (CARLA factual+matched-CF w/ GT) | PO (reasoning/editing metrics) | PO (contrastive rewards) | AO (none) | AO (curated GIFs only) | PO (consistency rewards) | PO (route-change rate) | PO (minimally-different quadruples) | ? | ? |
| RealityBench (real-image set) | PO | **SO** (occupies controlled CF benchmark w/ GT) | PO (RVEBench/FiVE) | PO | AO | AO | AO | AO | **SO** (real paired CF VideoQA) | ? | ? |
| CausalPairs (synthetic paired + masks) | PO (forked-state re-renders assumed) | **SO** (CARLA controlled pairs) | AO | AO | AO | AO | AO | AO | PO | ? | ? |
| Reward + best-of-N/CEM search | PO (verifiable reward proposed) | PO (training-free pipeline) | AO | **SO** (branch-reward post-training) | AO | AO | **SO** (GRPO consistency training) | AO | AO | ? | ? |
| Controller / RL (Phase D/E) | PO (post-training deferred) | AO | AO | **SO** | AO | AO | **SO** (GRPO) | AO | AO | ? | ? |
| Hero demo (synchronized A/B) | AO | AO | AO | AO | AO (closed preview, no pairs) | AO | AO | AO | AO | ? | ? |

## 2. Claim-by-claim evidence ledger

| Claim | Panelist(s) | Label | Identifier | Agreement | Contradictions |
|---|---|---|---|---|---|
| Twin Rollouts formalizes noise-coupled branching, locality metric, CF-reward; experiments "forthcoming," grid-world existence proof only | B, D, F | VERIFIED | 2608.08982 | Unanimous among auditors | None on substance |
| Internal red-team citation (shared-prefix Cosmos-Predict-2 CF synthesis @ 2604.20460) is misattributed; identifier = CCTVBench VideoQA benchmark | D, A | VERIFIED (direct fetches, independent) | 2604.20460 | 2+ | Contradicts internal project note — must be purged |
| Driving-CF formalizes abduction–action–prediction; CARLA GT benchmark; direct prediction fails; training-free pipeline; has experiments | D, A | VERIFIED | 2608.11601 | 2+ | Emphasis only |
| PersistWorld: RL post-training branching K=16 continuations sharing actions/varying noise | D | VERIFIED (ECCV 2026 venue unverified) | 2603.25685 | Unique | None |
| CWMDT: LLM-edited digital twins condition video diffusion; open-loop editing-based | D, A, F | VERIFIED | 2511.17481 | Unanimous | None |
| Genie 3 ships mid-rollout text events, marketed as "what if"; closed, no pairs | F, A | VERIFIED (official blog) / C: capability UNVERIFIED unusable | DeepMind blog Aug 2025 | 2+ | Evidentiary status disputed |
| EVOKE: per-chunk prompt schedules implemented; seed knob exposed; persistent state bank; branching NOT implemented | C | VERIFIED (code/docs/HF) | 2608.13546, AlayaLab/Evoke | Unique | Confirms CLAIMS.md C004 |
| No published noise-coupled mid-rollout branch pairs w/ per-sample verifiable locality in a full interactive video WM | D, A, F | Negative result (absence ≠ proof) | — | Unanimous | None |
| No shipped synchronized-A/B branch product; no prior best-of-N-over-intervention-schedules | F | Negative result | — | Unique | None |
| TR's reward defined-not-validated; viewpoint-moving interventions make locality vacuous | B | VERIFIED | 2608.08982 | Unique | Supports search-before-RL |
| Matrix-Game 2.0 removed text branch | C | VERIFIED | SkyworkAI/Matrix-Game | Unique | Key backend negative |
| SL-FM matched-prefix + controlled-divergence protocol (policy domain) | A | VERIFIED | 2607.10206 | Unique | None |
| IC-World GRPO consistency rewards across parallel rollouts | A | VERIFIED (repo checked) | 2512.02793 | Unique | None |
| Counterfactual-controllability position paper | D: LIKELY / A: VERIFIED | mixed | 2606.24152 | 2+ | Verification-level conflict |
| Benchmark lane crowded (Omni-WorldBench, WBench, CRONOS, WorldExam, YoCausal) | F | VERIFIED (abstracts) | various | Unique | None |
| No Cosmos-Predict-2 CF paper exists; README "coming soon" | A | VERIFIED | nvidia-cosmos/cosmos-predict2 | Unique | Reinforces D |

## 3. Disagreements (preserved verbatim)

1. **Genie 3 evidentiary status.** F/A treat blog-shipped claims as verified prior art; C refuses: "no public checkpoints or inference path; any capability claim about them is UNVERIFIED and unusable for our purposes."
2. **arXiv:2606.24152 verification level.** D: LIKELY (search excerpts); A: VERIFIED (abs fetched).
3. **Closest-threat ranking.** D: 2608.11601 closer than Twin Rollouts ("has experiments"); F: Twin Rollouts kills formalism claims, gap = empirical instantiation.
4. **Novelty-window breadth.** F: composition-only → engineering; C: core contribution "unoccupied territory"; D: narrow but real window.
5. **Backend bet.** C: EVOKE primary (state-bank deepcopy fork, untested); F: open-oasis/MineWorld preference. None endorses the other.
6. **PersistWorld weighting.** D elevates to closest prefix-branching precedent; A/B mention only via TR §4.
7. **Tier-C mechanism interventions.** F: unclaimed anywhere but too risky for 48h.

## 4. Synthesis summary

**(a) Surviving candidates:** (1) first executed measured demonstration of noise/prefix-coupled twin branches on a released pretrained interactive video WM with locality vs naive-edit controls; (2) coupling-off ablation as quantified negative control; (3) best-of-N/CEM over intervention schedules (reward-validation open per B).

**(b) Strongest ABANDON argument (F):** every component exists in resolved primary sources; exact formalization published 10 Aug 2026; 2608.11601 provides controlled CF benchmark with GT and experiments; search phases ≈ prompt tuning; without coupling minimal-change ≈ masked regeneration; benchmark lanes crowded.

**(c) Strongest CONTINUE argument (D+C+F convergence):** three sealed independent searchers found zero implementations of the full combination; sole formalizer defers scale-up/validation; concrete fork mechanism exists (EVOKE bank deepcopy + shared prefix + seed); survives if re-anchored from formalism to executed measurement under predeclared gates.

**(d) Unresolved requiring verification:** What-If World ID; CG-World ID/status; EVOKE bank-deepcopy comparability (state leakage, eviction); noise coupling feasibility beyond chunk 0; Yume 1.5 mid-rollout events in released code; MineWorld checkpoint availability; unofficial TR code; TR v2 monitoring; 2606.24152 level reconciliation.
