# Source Index

This is a convenience index, not a substitute for re-verification.

## OpenCode (checked 2026-08-24)

- Config JSON Schema (authoritative): https://opencode.ai/config.json
- Agents: https://opencode.ai/docs/agents
- Permissions: https://opencode.ai/docs/permissions
- Config: https://opencode.ai/docs/config
- Skills: https://opencode.ai/docs/skills
- Server API: https://opencode.ai/docs/server/
- SDK: https://opencode.ai/docs/sdk/
- Custom tools: https://opencode.ai/docs/custom-tools/
- CLI / upgrade: https://opencode.ai/docs/cli/

## Causal/world-model research (all checked 2026-08-24 via sealed novelty panel + STAGE 5 adjudication unless noted)

| Source | Identifier / URL | Checked | License / access caveats |
|---|---|---|---|
| Twin Rollouts (formalism; v1 formal-only) | https://arxiv.org/abs/2608.08982 | 2026-08-24 (full HTML) | arXiv non-exclusive license; no code/data links as of check |
| Driving counterfactual prediction | https://arxiv.org/abs/2608.11601 | 2026-08-24 (abstract) | standard arXiv |
| What-If World | https://arxiv.org/abs/2605.27589 | 2026-08-24 (abstract, adjudicator) | standard arXiv |
| CG-World | https://arxiv.org/abs/2607.26452 | 2026-08-24 (full HTML Table 3) | dataset gated on acceptance; noncommercial; raw L3 controlled access |
| CWMDT | https://arxiv.org/abs/2511.17481 | 2026-08-24 | standard arXiv |
| PersistWorld | https://github.com/Jai2500/PersistWorld ; arXiv:2603.25685 | 2026-08-24 (repo fetch by orchestrator) | MIT; ECCV 2026 venue self-reported at official repo |
| CoCo | https://arxiv.org/abs/2608.04653 | 2026-08-24 | standard arXiv |
| CSVC | https://arxiv.org/abs/2506.14404 | 2026-08-24 | standard arXiv |
| CounterScene | https://arxiv.org/abs/2603.21104 | 2026-08-24 | standard arXiv |
| SL-FM (matched-prefix interventions, policy domain) | https://arxiv.org/abs/2607.10206 | 2026-08-24 | standard arXiv |
| IC-World | https://arxiv.org/abs/2512.02793 ; github.com/wufan-cse/IC-World | 2026-08-24 | code repo verified |
| ShareVerse | https://arxiv.org/abs/2603.02697 | 2026-08-24 | abstract only |
| CCTVBench (**NOT** Cosmos-Predict-2 CF synthesis — misattribution purged per C018) | https://arxiv.org/abs/2604.20460 | 2026-08-24 ×3 independent fetches | VideoQA benchmark only |
| Genie 3 "promptable world events" (capability claim exists; closed system) | https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/ | 2026-08-24 | closed preview; no checkpoints |
| EVOKE paper | https://arxiv.org/abs/2608.13546 | 2026-08-24 | standard arXiv |
| EVOKE code | https://github.com/AlayaLab/Evoke | 2026-08-24 (README + inference docs) | Apache-2.0; `diffusers` pinned to dev fork not on PyPI; **both depth backends (ViGeo AND Depth-Anything-3) CC-BY-NC-4.0 = noncommercial**; no fork API upstream |
| EVOKE model | https://huggingface.co/AlayaLab/Evoke | 2026-08-24 | distilled checkpoints v2v-only training (i2v/t2v zero-shot) |
| Yume | https://arxiv.org/abs/2507.17744 ; Yume-1.5 arXiv:2512.22096 ; github.com/stdstu12/YUME | 2026-08-24 | mid-rollout event editing UNVERIFIED in released code |
| Matrix-Game 2.0 / 3.0 | github.com/SkyworkAI/Matrix-Game ; arXiv:2604.08995 | 2026-08-24 | MIT; MG2.0 has NO text branch (architecturally unfit); MG3.0 "40 FPS" needs 8×GPU cluster |
| open-oasis | github.com/etched-ai/open-oasis | 2026-08-24 | MIT; 500M weights; action-conditioned only |
| cosmos-predict2 | github.com/nvidia-cosmos/cosmos-predict2 | 2026-08-24 | paper "coming soon" — no CF literature exists for it |
| CoPhy (paired do-intervention dynamics precedent) | https://arxiv.org/abs/1909.12000 | 2026-08-24 (abstract, panelist F) | ICLR 2020; synthetic, non-interactive |
| Counterfactual World Modeling (Bear et al.) | https://arxiv.org/abs/2306.01828 | 2026-08-24 (repo) | masked-predictor lineage |
| CF-controllability position paper | https://arxiv.org/abs/2606.24152 | 2026-08-24 | verification level disputed in panel (LIKELY vs VERIFIED); reconcile before citing |
| RLVR-World | https://arxiv.org/abs/2505.13934 | earlier check | standard arXiv |

Full evidence narratives: `fanin/2026-08-24-novelty/{sealed-reports,synthesis,adjudication}.md`.

Any agent using a source for a public claim should revisit the canonical source at the time of use.
