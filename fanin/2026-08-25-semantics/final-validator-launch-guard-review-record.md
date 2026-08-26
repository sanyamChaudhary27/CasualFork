# Final Validator / Launch-Guard Sealed Delta Review (2026-08-26)

Base reviewed: `68ccb535c161f7b71b9c480499951913ca59f28b` plus the uncommitted validator/launch-guard correction (`5bd2ffa9…`). No GPU, weight, model-load, or rollout evidence was used. Seal order: M and G were dispatched simultaneously in fresh mutually blind contexts; neither was provided previous review conclusions. Both inspected only the requested delta and relevant pinned source.

| Reviewer | Session | Verdict |
|---|---|---|
| M, coupling methodology | `ses_fc15e1004ffe4q6DX3kwDkbJtg` | `PATCH_INCOMPLETE` |
| G, implementation / GPU reproducibility | `ses_fc15dff71ffeIxhGF6Tr0jkmhS` | `PATCH_INCOMPLETE` |

## Converged findings

Both statically confirmed F10 per-run digest-to-ledger binding, F12 loaded-artifact validation, non-object JSONL rejection, and logging-only F08 counter removal. Both also independently found two concrete remaining defects:

1. **Guard bypass:** `harness/gpu01_prelaunch.py` is an independently executable CLI. No launcher wrapper requires its passing artifact before EVOKE is imported/constructed; patched engine code does not itself require a prelaunch artifact. A direct EVOKE launch can therefore bypass literal-manifest strictness.
2. **Config attestation gap:** `gpu01_prelaunch.py:42-60` validates patch/profile hashes but neither computes from resolved argv/relevant environment nor requires/compares `EVOKE_STRICT_CONFIG_SHA256`. The validator checks recorded declarations against the manifest, not actual launch inputs. A stale declared config hash can conceal a prohibited non-prompt configuration drift.

These defects violate the requested mechanical GPU-01 policy and make a false `STRICT_NOISE_COUPLED` certification possible despite otherwise sound noise witnesses. The review did not treat hypothetical polish as blocking; each objection is executable/certification-relevant and CPU-resolvable.

## Adjudication

Direct code confirms both findings. Final verdict: **PATCH_INCOMPLETE**. GPU-01 countersignature is **NOT GRANTED**. No broader redesign is authorized or started.

## Exact narrow next action

Implement a single wrapper that invokes prelaunch, requires/archive-binds `GPU01_PRELAUNCH_PASS`, then and only then executes the model command; compute canonical resolved config identity from the exact model argv plus strict-relevant environment, bind it to manifest and `EVOKE_STRICT_CONFIG_SHA256`, and have final validation/countersign require the prelaunch artifact and engine strict evidence. Add direct guard-bypass/stale-config negative fixtures, rerun CPU matrix, then obtain a fresh two-reviewer delta review.
