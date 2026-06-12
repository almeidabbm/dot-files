# Shared AI Workflow Rules

## Git & Branching

- Never commit directly to `main` or trunk. Before making any commits, check the current branch with `git branch --show-current`. If you are on `main`, create a branch first.
- Prefer Graphite CLI (`gt`) for branch management when available; fall back to plain `git` when it is not.
- Use `gt create -m "branch-name"` for stacked branches when `gt` is available. Use `git checkout -b branch-name` for independent work or as the fallback.
- Never push or submit (`git push`, `gt submit`) without explicit permission. Local commits are fine; remote actions require approval.
- Always sync trunk before starting new work: `gt sync` if available, otherwise `git fetch origin && git checkout main && git pull --rebase`.

## Graphite Availability

- Before running any `gt` command, check `command -v gt` and fall back to plain `git` if missing.
- Fallbacks:
  - `gt sync` -> `git fetch origin && git checkout main && git pull --rebase`
  - `gt create -m "branch-name"` -> `git checkout -b branch-name`
  - `gt log` -> `git log --oneline --graph --decorate --all -20`
  - `gt modify` -> `git commit --amend`
  - `gt restack` -> manual rebases per child branch
- If `gt` is missing, mention that stacked PR tooling will not auto-restack downstream branches.

## Worktrees

- Worktrees live inside the repo at `$(git rev-parse --show-toplevel)/.worktrees/<feature>/` and must stay gitignored.
- Create them from trunk: `git worktree add .worktrees/<feature> trunk`.
- After creating a worktree, symlink `.local` so it shares project intel with the main repo:
  - `ln -s ../.local .worktrees/<feature>/.local`
- Copy `.env*` and `.envrc` from the main repo into the worktree, ignoring missing files.
- Run `docker compose` from inside the worktree directory when compose files use relative paths.
- Remind the user to clean up finished worktrees with `git worktree remove .worktrees/<feature>`.

## Stacking Work

- For larger changes, break the work into a stack of small, reviewable PRs.
- Each branch in the stack must be independently understandable and must not break the codebase.
- Present the proposed stack decomposition before starting a big implementation so the user can adjust scope.
- Before creating each stacked branch, commit the current work and run the related tests.
- When amending a branch mid-stack, use `gt modify` if available; otherwise use `git commit --amend` and manually rebase downstream branches.
- If a restack or rebase hits conflicts, stop and show the conflicts instead of guessing through them.

## Commits

- Use Conventional Commits: `feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:`, `perf:`, `ci:`, `build:`.
- Keep subjects concise and under 72 characters.
- Use the body for why, not what.
- Never add `Co-Authored-By` trailers.

## Testing

- Before committing, run tests related to the changed files only.
- If the related test surface is unclear, stop and ask rather than running the whole suite by default.

## Active Task Convention

Per-task working memory lives at `$(git rev-parse --show-toplevel)/.local/active/<slug>/`. Each task has four files:

- `spec.md` - the design for the current task
- `plan.md` - the implementation plan or PR decomposition
- `notes.md` - running log plus status frontmatter
- `review.md` - pre-merge findings and hardening notes

`notes.md` frontmatter is the workflow source of truth:

```markdown
---
slug: YYYY-MM-DD-<kebab>
linear: <issue-id-or-empty>
size: quick | standard | big
status: spec | plan | implementing | review | ready-to-ship | merged | archived
last-updated: <ISO timestamp>
---
```

- Current task = the most recently modified folder under `.local/active/`.
- On archive, move `active/<slug>/` to `archive/<slug>/`.
- Durable architectural intelligence lives in `.local/system-map/` with prefixes `inv-`, `area-`, `danger-`, and `pitfall-`.

## Workflow Guidance

- When the user starts new work, mentions an issue, or wants to scope a feature, use the `start-task` workflow.
- When the user asks what they were working on or seems disoriented, use the `status` workflow.
- When implementation is done and tests pass, use the `pre-merge` workflow before shipping.
- When the user asks for a diff review, use the `code-review` workflow.
- After a PR is merged or the user wants to wrap up the task, use the `archive-task` workflow.

## Spec And Plan Files

- Specs and plans for the current task live in `.local/active/<current-slug>/spec.md` and `plan.md`, where the current slug is the most recently modified folder under `.local/active/`.
- These paths override the default output locations of planning-oriented Superpowers workflows. Do not save task specs or plans to `docs/`, `docs/plans/`, `../<repo>_plans/`, or any other external or repo-tracked location while the task is active.
- If `.local/active/` is empty, start the task first before writing a spec or plan.
- If `superpowers` is installed, it can help draft specs or plans, but these task-local files remain the source of truth.

## Per-Repo Gitignore

Every repo using this workflow should gitignore the working-memory and worktree folders:

```gitignore
.local/
.worktrees/
```

- Keep these rules version-controlled in the repo rather than relying on a global excludes file.

## Code Style

- Follow existing project conventions and patterns.
- Prefer functional patterns where appropriate.
- Keep changes minimal and focused on the task at hand.
- Do not add unnecessary annotations, comments, or docstrings to code you did not change.
