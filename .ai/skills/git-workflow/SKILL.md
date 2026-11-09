---
name: git-workflow
description: Personal Git conventions for trunk sync, single-PR features split into layered commits, when a change needs its own PR, worktrees under .worktrees/, and PR submission with a risk map. Load before starting implementation (trunk sync comes first), before the first branch, commit, worktree, or PR operation in a task, and when a rebase fails.
---

# Git Workflow

Repository branch policy takes precedence over these personal defaults. Check installed command help rather than assuming flags are unchanged.

## Branches And Sync

- Before starting implementation, and again when trunk moves, fetch origin and rebase onto `origin/<trunk>`. Inspect the working tree first and preserve existing changes.
- Determine the repository's actual trunk branch; `trunk` is a placeholder, not a required branch name.
- One feature, one branch: `git checkout -b <branch-name>`, or a worktree (below).
- If a rebase conflicts, stop and show the conflicts.

## Layered Commits

A feature ships as one PR; its commits are the review units. Each commit is one **layer**: a slice of the change that fails in one way and is reviewed in one way. [`LAYERS.md`](LAYERS.md) lists the common layers, how each fails, and how each is reviewed; read it before the first commit of a feature.

- Order commits by blast radius: mechanical prep first, then the catastrophic layers (data, access, domain logic, contracts), then the rest, UI last. A reviewer reads from the top and stops once the risk is behind them.
- Every commit builds and passes the related checks on its own. Tests travel in the commit whose code they cover.
- Mechanical changes (renames, moves, codegen, formatting, lockfiles, dependency bumps) get their own commits with no behaviour change, so the reviewer can skip them.
- Subject: Conventional Commit, scope is the feature. Body: why, then what breaks if this commit is wrong. Last line, a trailer naming the layer: `Layer: data`.
- For a larger feature, propose the commit plan (layer, one-line intent) before implementing so the user can adjust scope.
- Review fixes land as new commits on the affected layer (`git commit --fixup <sha>`), so "changes since last review" stays readable. Squash with `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash <base>` only when the repository merges with rebase; with squash-merge, leave them.

## When A Change Needs Its Own PR

Split by deploy order, not by size. A change goes in an earlier PR, merged and deployed first, when shipping it together with the code that uses it would break a rolling deploy or a rollback:

- **Migrations that old code cannot run against**: renames, drops, new NOT NULL without default, type changes, backfills. Use expand then contract: additive migration first, code next, cleanup last. Additive, backward-compatible migrations (new table, nullable column, index) stay in the feature PR.
- **Breaking contract changes** that external callers depend on (public API, SDK, CLI, MCP tools, file formats): ship the new shape alongside the old, migrate callers, then remove.
- **Config changes** that existing installs must set before the new code runs.

If the repository has a release-safety or compatibility check, its verdict decides.

## Pull Requests

- Open with `gh pr create`. The description leads with a **risk map**: each commit in a catastrophic layer, what could go wrong, and how it was verified. Every other layer gets one line naming its evidence (tests, screenshots, eval run). The repository's own list of catastrophic paths, when it has one, extends the defaults in `LAYERS.md`.
- In a public repository, keep the risk map in the project's private state folder (`project-state` skill) instead, and give the PR a plain description of the change.
- Point the fresh-context review agent at the risk map and the risky commits, not the whole diff.

## Stacks (opt-in)

Use `gh stack` only when the user asks for stacked PRs. Check `gh extension list | grep -q gh-stack` and read `gh stack --help`; exit code `9` means the repository does not support stacking, so say so and fall back to dependent branches with `gh pr create --base <parent-branch>`.

## Worktrees

- Put worktrees at `$(git rev-parse --show-toplevel)/.worktrees/<feature>/`.
- Base new work on current trunk. Create a feature branch in the worktree with `git worktree add -b <branch-name> .worktrees/<feature> <trunk>`; if the feature branch already exists, use `git worktree add .worktrees/<feature> <branch-name>`. Avoid trying to check out a trunk branch already in use by the main checkout.
- Copy `.env*` and `.envrc` from the main repo into the worktree, ignoring missing files. Keep those local files out of commits and worker reports.
- Run `docker compose` from inside the worktree when compose files use relative paths.
- Remind the user to clean up finished worktrees with `git worktree remove .worktrees/<feature>`.

Every repository using worktrees must version-control these ignore rules, rather than relying on global excludes:

```gitignore
.local/
.worktrees/
```
