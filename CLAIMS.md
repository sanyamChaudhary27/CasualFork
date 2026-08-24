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
| C003 | EVOKE supports camera-indexed persistent world state and per-chunk re-prompting. | UPSTREAM_REPORTED | AlayaLab/Evoke official repo/model card | Attribute to EVOKE until reproduced. |
| C004 | EVOKE's released distilled i2v path is in-distribution. | REJECTED | Official model card says distilled models were trained on v2v only; i2v/t2v are zero-shot. | Never claim this. |
| C005 | Yume supports image-conditioned interactive world generation with camera/keyboard control. | UPSTREAM_REPORTED | Official YUME repo/paper | Attribute to Yume until reproduced. |
| C006 | Twin Rollouts formalizes noise-coupled counterfactual branching and locality evaluation. | UPSTREAM_REPORTED | arXiv:2608.08982 | "Twin Rollouts proposes/formalizes..." not "demonstrates" unless experiments appear. |
| C007 | CausalFork can preserve an identical prefix. | PROPOSED | G4 pending | No public claim yet. |
| C008 | CausalFork can change one requested condition while preserving unrelated geometry. | PROPOSED | G6 pending | No public claim yet. |
| C009 | Search/evolution improves counterfactual branch quality. | PROPOSED | G7 pending | No public claim yet. |
| C010 | A learned controller/RL improves over search. | PROPOSED | G8 pending | No public claim yet. |
| C011 | The final system runs in real time. | PROPOSED | end-to-end measurement pending | Do not use "real-time" yet. |

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
