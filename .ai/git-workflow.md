# Git Workflow

Read before branch, stack, worktree, commit, or PR operations. Repository branch policy takes precedence over these personal defaults. Check installed command help rather than assuming flags are unchanged.

## Branches And Sync

- Before starting implementation, and again when trunk moves, sync with current trunk. Inside a stack, use `gh stack sync`; otherwise fetch origin and rebase onto `origin/<trunk>`.
- Determine the repository's actual trunk branch; `trunk` below is a placeholder, not a required branch name. Inspect the working tree before syncing and preserve existing changes.
- Check the stacking extension before using it: `gh extension list | grep -q gh-stack`. If needed, install with `gh extension install github/gh-stack`.
- Read `gh stack --help` and the relevant command help. Start a stack with `gh stack init <branch-name>`; add a layer with `gh stack add -m "message" <branch-name>`.
- For standalone work or when stacking is unavailable, use `git checkout -b <branch-name>`.

## Stacked Pull Requests

- For larger changes, present a proposed stack of small, independently understandable PRs before implementing so the user can adjust scope. Each layer must leave the codebase working.
- Before creating the next layer, run the related checks and commit the current work.
- Submit with `gh stack submit`. Noninteractive submission creates draft PRs by default; pass `--open` for ready-for-review PRs. The interactive editor has its own draft toggle.
- To amend a layer, use `git commit --amend`, then `gh stack rebase --upstack` so downstream layers pick up the change.
- `gh stack modify` is the interactive restructure UI for dropping, folding, reordering, or renaming layers; it is not an amend. It requires a clean working tree, linear history, and no rebase in progress.
- `gh stack init` enables `git rerere`, which can replay a previously resolved conflict. If a rebase conflicts, stop and show the conflicts.

Stacking is enabled per repository. Exit code `9` from a `gh stack` command means the repository does not support it. State that limitation and use these fallbacks:

| Operation | Fallback |
| --- | --- |
| Create branch | `git checkout -b <branch-name>` |
| View branches | `git log --oneline --graph --decorate --all -20` |
| Submit | `gh pr create --base <parent-branch>` per branch, in dependency order |
| Sync | `git fetch origin`, then rebase each child onto its updated parent |
| Amend | `git commit --amend`, then rebase downstream branches in order |

When falling back, explicitly say that downstream branches will not be rebased automatically and the PRs will not be linked as a stack on GitHub. Distinguish unsupported stacking from authentication or other command failures.

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
