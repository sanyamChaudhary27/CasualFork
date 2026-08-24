---
name: git-worktree-isolation
description: Use ONLY when two or more agents must implement changes in parallel without corrupting the same files - isolates each builder in its own Git worktree and branch with explicit file ownership, per-builder verification, and orchestrator-driven merges.
---
# Git Worktree Isolation

Use only when parallel edits are genuinely valuable.

1. Ensure the main worktree is clean or changes are intentionally committed/stashed.
2. Create one branch/worktree per builder with clear ownership.
3. Give each agent the exact worktree path and files it owns.
4. Do not edit the same file in two worktrees unless planning an explicit manual merge.
5. Each builder runs its own verification and commits a small coherent change.
6. Reviewer inspects commits/diffs before merge.
7. Orchestrator merges one branch at a time and reruns integration checks.

Never use worktrees as an excuse to let multiple agents redesign the same notebook concurrently.
