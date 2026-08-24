# Claim Ledger

Every public technical claim must point to evidence here before it appears in a README, post, demo overlay, or pitch.

## Status values

- `PROPOSED` — hypothesis/design intent.
- `UPSTREAM_REPORTED` — official paper/repo/model card reports it; not reproduced by us.
- `REPRODUCED` — we independently reproduced it with recorded experiment evidence.
- `PROJECT_VERIFIED` — our own implementation/measurement supports the claim.
- `REJECTED` — evidence failed; do not repeat.

## Initial ledger

| ID | Claim | Status | Evidence | Public wording allowed |
|---|---|---|---|---|
| C001 | OpenCode V2 can run subagents as fresh child sessions, including background execution. | UPSTREAM_REPORTED | Official OpenCode V2 Agents docs, checked 2026-08-24 | "OpenCode supports fresh child-session subagents." |
| C002 | OpenCode Server API can create/list/fork sessions and send async prompts. | UPSTREAM_REPORTED | Official OpenCode Server docs, checked 2026-08-24 | "OpenCode exposes programmatic session APIs." |
| C003 | EVOKE supports camera-indexed persistent world state and per-chunk re-prompting. | UPSTREAM_REPORTED | AlayaLab/Evoke official repo/model card; detailed by C015–C017 | Attribute to EVOKE until reproduced. |
| C004 | EVOKE's released distilled i2v path is in-distribution. | REJECTED | Official model card says distilled models were trained on v2v only; i2v/t2v are zero-shot. | Never claim this. |
| C005 | Yume supports image-conditioned interactive world generation with camera/keyboard control. | UPSTREAM_REPORTED | Official YUME repo/paper | Attribute to Yume until reproduced. |
| C006 | Twin Rollouts owns the formalism for noise-coupled counterfactual branching and locality evaluation. | UPSTREAM_REPORTED | arXiv:2608.08982 v1 full text, checked 2026-08-24 by sealed panel + adjudicator | "Twin Rollouts formalizes/proposes..." — never "demonstrates at scale." |
| C007 | CausalFork can preserve an identical prefix. | PROPOSED | G4 pending | No public claim yet. |
| C008 | CausalFork can change one requested condition while preserving unrelated geometry. | PROPOSED | G6 pending | No public claim yet. |
| C009 | Search/evolution improves counterfactual branch quality. | PROPOSED | G7 pending; conditional on SC1 success | No public claim yet. POST-SC1 stretch work. |
| C010 | A learned controller/RL improves over search. | PROPOSED | G8 pending; conditional on SC1+G7 success | No public claim yet. POST-SC1 stretch work. |
| C011 | The final system runs in real time. | PROPOSED | end-to-end measurement pending | Do not use "real-time" yet. |
| C012 | Twin Rollouts experimental status: v1 contains no full experiments — abstract says "experiments are forthcoming"; §3 is a deterministic grid-world existence proof; reward R defined but unvalidated; viewpoint-moving interventions make locality L vacuous pending camera-compensated comparison. | UPSTREAM_REPORTED | arXiv:2608.08982 v1 full text fetched 2026-08-24 (panelist B + adjudicator independently) | "Formal framework with forthcoming experiments; grid-world existence proof only." Never imply empirical video-scale results exist. |
| C013 | What-If World (arXiv:2605.27589) provides 319 single-variable prompt-intervention pairs on real frames with a preservation rubric (APEO incl. "preserves the shared scene"); best model ~52%, best open-source ~28%. | UPSTREAM_REPORTED | Adjudicator-fetched abstract 2026-08-24 | Attribute to What-If World; cite when discussing paired-intervention evaluation. |
| C014 | CG-World (arXiv:2607.26452) contains exactly 5,000 strict mechanism + 5,000 strict action counterfactual branches (1,000 same-root families) with recorded invariant sets; dataset access gated on acceptance, noncommercial license, controlled raw access — unusable as our eval infrastructure today. | UPSTREAM_REPORTED | Full-text Table 3 fetched 2026-08-24 by adjudicator | State facts + caveats together; never present CG-World as available infrastructure. |
| C015 | EVOKE implements scheduled per-chunk re-prompting during ongoing generation (`MODE=segment`, `schedule_*.json`; switch granularity = chunk boundary). | UPSTREAM_REPORTED | Repo README + inference docs code-inspected 2026-08-24 (panelist C + adjudicator); not executed by us | "EVOKE's released code supports..." until we reproduce. |
| C016 | EVOKE exposes run-level seed control (`SEED` launcher knob); branch-level noise coupling is not exposed upstream. | UPSTREAM_REPORTED | Repo docs inspected 2026-08-24 | Distinguish run-level SEED from branch-level coupling explicitly. |
| C017 | EVOKE provides no upstream branch/fork API as of 2026-08-24. | UPSTREAM_REPORTED | Absence verified across repo README/docs by panelist C + adjudicator; absence claims are date-stamped and fragile | "...no fork API in the public repo/docs as of <date>." |
| C018 | The prior internal association of arXiv:2604.20460 with shared-prefix Cosmos-Predict-2 counterfactual synthesis is WRONG; that identifier is CCTVBench, a VideoQA benchmark pairing real clips with world-model-generated counterfactual counterparts. No Cosmos-Predict-2 CF paper exists ("coming soon" per official README). | REJECTED | Two independent panelist fetches + adjudicator fetch, 2026-08-24 | Purge the old association everywhere; if citing 2604.20460, cite it only as CCTVBench. |
| C019 | SC1: first executed demonstration of prefix/noise-coupled twin branches inside a released pretrained interactive video world model under a deliberate mid-rollout intervention, measuring per-sample locality against coupling-off controls. | PROPOSED | GF0 feasibility pending → G-gates; negative-search result logged 2026-08-24 (fanin/2026-08-24-novelty/); ablation defined in SPEC.md §2b | FORBIDDEN until verified + refreshed novelty audit: any use of "first". Allowed interim: "we aim to demonstrate / propose." |
| C020 | SC2: uncoupled/naive prompt-edit forks produce materially more unintended divergence than properly coupled branches, under a predeclared comparison. | PROPOSED | Predeclared ablation defined in SPEC.md §2b; execution pending | No public claim until measured against the predeclared gate. |

## New claim template

```text
ID:
Claim:
Status:
Source / experiment:
Hardware/version if measured:
Exact scope:
Known counterexamples:
Allowed public wording:
Forbidden stronger wording:
Owner:
Last verified:
```
