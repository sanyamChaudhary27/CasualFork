# Adjudication Report — Sealed Novelty Panel, 2026-08-24 (STAGE 5)

Session: ses_fcb4bc763ffe5LZCUfv2Gd77Ad (reviewer) · Status SUCCESS
Input deviation recorded: synthesis text was NOT available to the adjudicator (orchestrator persistence defect, see synthesis.md header). Adjudication performed directly against primary sources and verification list V1–V7.

## Adjudication verdicts

| Claim | Post-adjudication status | Independent evidence | Notes |
|---|---|---|---|
| V1 Twin Rollouts arXiv:2608.08982: v1 10 Aug 2026; formal-only; "experiments are forthcoming"; grid-world existence proof; reward defined-not-validated; viewpoint-vacuity caveat | **VERIFIED** | Fetched abs + full HTML: title/authors/date/49KB match; abstract ends "experiments are forthcoming"; §3 "existence proof" in deterministic grid world ("Scale-up…deferred to the next revision"); Def. 3 R=−(λ_O·O+λ_L·L) with zero experimental validation; §5 viewpoint-vacuity statement; no code/data links | None material |
| V2 2608.11601 = driving CF-prediction paper WITH experiments + controlled benchmark w/ ground truth | **VERIFIED** | Zhang et al., 12 Aug 2026; "controlled simulation benchmark with factual outcomes and matched counterfactual outcomes"; two world models; training-free pipeline | None |
| V3 2604.20460 = CCTVBench VideoQA benchmark, NOT shared-prefix Cosmos-Predict-2 synthesis | **CONFIRMED misattribution** | Fetched abs: CCTVBench, Zhou et al., 22 Apr 2026; pairs real accident clips with world-model-generated CF counterparts for contrastive decoding | Purge citation wherever it lives |
| V4 What-If World ≈ 2605.27589; paired single-variable prompt interventions on real frames + preservation rubric | **VERIFIED** | Cai et al., 26 May 2026; 319 prompt pairs on real nuScenes/DROID frames, one variable varied; APEO rubric incl. Environment ("preserves the shared scene"); best model 52%, open-source ~28%; cited as [2] in Twin Rollouts itself | E's infra failure fully remediated by adjudicator |
| V5 CG-World ≈ 2607.26452; mechanism-CF branches with invariant sets | **VERIFIED with precision** | Full HTML Table 3: exactly **5,000 strict mechanism CF branches + 5,000 strict action CF branches**, 1,000 same-root families, invariant sets recorded; strict-CF preserves exogenous context | Panel missed: dataset gated on paper acceptance; noncommercial license; raw L3 controlled access → NOT usable as evaluation infrastructure today |
| V6 Genie 3 mid-rollout "promptable world events" claim exists via official blog | **VERIFIED** | DeepMind blog (5 Aug 2025): "Promptable world events" section — weather changes/object spawning; explicitly framed as "counterfactual, or 'what if' scenarios"; limited research preview; events "not necessarily performed by the agent itself" | Claim-existence verified; capability remains closed/unusable |
| V7 EVOKE segment mode + SEED knob real; branching absent | **VERIFIED** | Repo README + scripts/inference/README.md: `MODE=segment` + `schedule_*.json` (switch at chunk 3 of 6); `SEED` documented; state bank write/read/evict; distilled models v2v-only; diffusers dev-fork pin; no fork API anywhere | Correction: BOTH depth backends (ViGeo AND Depth-Anything-3) are CC-BY-NC-4.0 — noncommercial scope wider than panelist C reported |

Sweep found no Twin Rollouts v2, no executed implementation of the combination, nothing closer than the panel's list. PersistWorld's "ECCV 2026" venue tag remains UNVERIFIED (content corroborated via Twin Rollouts §4).

## Errors or overclaims caught

1. Missing synthesis document at STAGE 5 (process violation — orchestrator).
2. License scope understated: both EVOKE depth backends noncommercial.
3. CG-World treated as available prior art without noting unreleased/noncommercial status.
4. Minor: Report D's "ECCV 2026" venue unverified.

## Ruling on surviving contributions

- **SC1:** First *executed* demonstration of noise/prefix-coupled twin branches (shared prefix + shared future exogenous noise + deliberate mid-rollout intervention) inside a publicly released pretrained interactive video world model, with per-sample locality measured against coupling-off controls. Falsified by any shipped fork-with-shared-noise implementation or Twin Rollouts v2 with experiments before ours.
- **SC2:** Quantified negative-control result showing uncoupled prompt-edit forks exhibit global out-of-mask drift vs coupled branches (predeclared divergence-ratio gate).

Everything else is dead: formalism (Twin Rollouts), CF-benchmark novelty (11601/What-If World/CCTVBench), intervention-conditioned CF video (CWMDT), prefix-branching RL (PersistWorld), mid-rollout intervention as a capability claim (Genie 3, EVOKE).

## Abandon-vs-continue ruling

**CONTINUE — narrowly scoped to SC1+SC2, one backend, predeclared gates.** Grounding: ingredients exist separately (all verified); the executed combination is unoccupied as of today; Twin Rollouts' explicit deferral creates a time-boxed window; EVOKE provides implemented schedules + documented SEED + serializable state bank (fork mechanism still an untested hypothesis); What-If World's ≤52% scores independently confirm naive single-variable interventions fail — motivating the measurement. CPU-first risks before GPU spend: noise coupling beyond chunk 0 may be unreachable through EVOKE's launcher (fallback label: "prefix-shared/seed-matched", gate on search-vs-naive); noncommercial depth backends block commercial framing. Do NOT spend GPU on: new formalism, new benchmark suites, viewpoint-moving interventions (vacuous locality), or RL (reward unvalidated; search-before-RL applies).

## Files that SHOULD change (NOT edited)

- RESEARCH.md: add 2608.11601, 2605.27589, 2607.26452, Genie-3 blog, EVOKE repo facts; mark PersistWorld venue UNVERIFIED.
- CLAIMS.md: purge/correct 2604.20460-as-synthesis citations; add V2/V4/V5 findings; narrow C003 to "per-chunk re-prompting (segment mode), run-level SEED."
- SPEC.md: restrict interventions to viewpoint-preserving class pending camera-compensated comparison; add coupling-infeasibility fallback gate; note CG-World unusable as eval infrastructure (unreleased, NC license).
- SOURCES.md: register all seven identifiers with fetched dates and license notes (CC-BY-NC-4.0 ×2 backends; diffusers dev-fork pin).
