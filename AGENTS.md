# CausalFork Project Constitution

## Mission

Build and honestly evaluate **CausalFork / RealityFork**: counterfactual interactive world generation in which a factual and counterfactual branch share the same past and future camera trajectory while a deliberate intervention changes as little else as possible.

The project succeeds only if it produces both:

1. a visually extraordinary, instantly understandable demo; and
2. evidence that the result is more than a UI wrapper around a pretrained world model.

## Authority order

When sources disagree, use this order:

1. Reproduced local experiment with logged environment and artifacts.
2. Upstream source code / model card / official documentation at a pinned commit or version.
3. Paper text and appendices.
4. Official project page or maintainer statement.
5. Third-party benchmark/report.
6. Search snippet, social post, or model memory.

Never convert a lower-tier claim into a higher-tier fact without verification.

## Work protocol

### Evidence before architecture

Before introducing a dependency, model, metric, or performance claim:

- identify its source;
- record the exact version/commit when practical;
- distinguish **reported** behavior from **reproduced** behavior;
- record license constraints;
- record expected GPU/CPU/RAM/storage requirements;
- add material claims to `CLAIMS.md`.

### Notebook-first until the core effect is proven

Until experiment Gate G6 passes, implementation priority is:

1. reproducible notebook / script;
2. logged artifacts and metrics;
3. backend abstraction;
4. only then frontend/product work.

No agent should spend significant time on auth, accounts, payments, deployment polish, or a rich frontend before G6.

### GPU-seconds are scarce; reasoning tokens are cheap

Before a paid GPU run, require a written hypothesis, exact command/notebook cell, expected output, stop condition, and fallback. Debug package imports, data plumbing, prompts, and CPU-testable logic without paid accelerators whenever possible.

Paid runs additionally require a completed GPU experiment proposal (COMPANY.md "GPU experiment proposal gate") with reviewer countersignature before launch.

### One writer per file

Parallel research is encouraged. Parallel edits to the same file are forbidden.

If two implementation tasks truly need to proceed in parallel, use separate Git worktrees/branches and invoke the `git-worktree-isolation` skill. The orchestrator merges verified commits.

### Subagent delegation

The `orchestrator` should delegate whenever independent expertise or adversarial review can reduce error. For material decisions, prefer at least two independent opinions plus a reviewer.

Every delegated task must return:

- **Conclusion** — one sentence.
- **Evidence** — exact files, commits, URLs, experiment IDs, or measurements.
- **Uncertainty** — what is not established.
- **Recommendation** — concrete next action.
- **Blockers** — only real blockers.

Researchers and reviewers do not edit project files unless their agent definition explicitly allows it.

### Major decisions require dissent

For backend choice, novelty claim, reward design, or compute spend:

1. commission an advocate;
2. commission a skeptic / red-team;
3. compare evidence;
4. orchestrator records the decision in `DECISIONS.md`.

### Context independence (sealed review)

For material research decisions, independent reviewers must form and record their preliminary judgment BEFORE receiving any other panel member's conclusion. Independence means fresh-context plus conclusion-blind; role naming alone does not establish independence.

The orchestrator must record the seal order — who was dispatched, in what order, when each report returned and was sealed — so retrospective fake consensus is detectable. Reports are revealed simultaneously only after every usable independent report is sealed (see COMPANY.md "Sealed review protocol").

### Search before RL

Do not add PPO/GRPO/RL merely to make the project sound advanced. First prove a reward function correlates with desired counterfactual quality using best-of-N or evolutionary/CEM search. RL/controller training is allowed only after the reward is demonstrably useful.

### No foundation-model training from scratch

Our 48-hour contribution is the branching/evaluation/search/controller system. Full world-model pretraining is out of scope unless the project is explicitly re-scoped later.

## Research invariants

A valid counterfactual comparison must strive to hold fixed:

- pre-fork generated prefix;
- future camera trajectory;
- random seed/noise where the backend permits coupling;
- all non-intervened world properties that can reasonably be preserved.

For synthetic simulator scenes, use ground-truth branch state and masks whenever possible instead of a learned judge.

## Reproducibility contract

Every serious experiment must record at minimum:

- experiment ID and timestamp;
- git commit;
- upstream model/repo commit or model revision;
- hardware/GPU and VRAM;
- CUDA, driver, PyTorch, Python;
- resolution, frame count, steps, dtype;
- input asset hash;
- prompt/intervention;
- camera/control trajectory;
- seed/noise policy;
- wall time and peak VRAM;
- output paths/hashes;
- metric vector;
- human notes;
- pass/fail against a predeclared gate.

A visually good clip without this record is a demo candidate, not research evidence.

Gate status vocabulary: without independent reviewer verification of the evidence, a gate is UNVERIFIED, never PASS. The experiment owner cannot approve its own gate; the orchestrator adjudicates only after reviewer verification.

## Claim hygiene

Never say:

- "real-time" without measured end-to-end latency/FPS and hardware;
- "causal" when the system only did prompt editing without a controlled intervention protocol;
- "same world" without an explicit preservation test;
- "RL improved it" without a baseline and held-out comparison;
- "state of the art" without a named benchmark and comparable protocol;
- "we trained" when we only ran inference or parameter search.

Use `CLAIMS.md` as the public-claim ledger.

## Code and Git safety

- Never `git push` unless the user explicitly asks.
- Never rewrite public history.
- Never run destructive filesystem commands without explicit approval.
- Never delete a working baseline while optimizing it.
- Keep upstream repos or large model weights out of Git unless intentionally vendored.
- Store generated videos/checkpoints under ignored artifact directories once the repo exists.

## Stop conditions

Stop and escalate instead of thrashing when:

- the official upstream sample cannot be reproduced after environment verification;
- an OOM persists after the `oom-recovery` ladder;
- a claimed model capability exists only in a paper/demo but not released code/weights;
- license terms conflict with intended use;
- a metric rewards obviously worse videos;
- two consecutive paid-GPU runs fail for the same unexamined reason.

## Definition of Tier-1 demo success

At minimum, one hero sequence must show:

1. one ordinary source image;
2. movement beyond the source view;
3. a coherent generated environment;
4. a fork at a clear point;
5. identical or provably shared prefix;
6. the same future camera path in both branches;
7. a conspicuous requested intervention in one branch;
8. strong preservation of unrelated geometry/content;
9. synchronized A/B presentation;
10. an honest technical explanation of what is pretrained versus ours.

The branch is the project. WASD is presentation.
