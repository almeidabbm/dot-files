# Shared AI Workflow Rules

## Git & Branching

- Never commit directly to `main` or trunk. Before making any commits, check the current branch with `git branch --show-current`. If you are on `main`, create a branch first.
- Use GitHub's native stacked pull requests (`gh stack`) for branch management whenever the repo supports it; fall back to plain `git` plus `gh pr` when it does not.
- Use `gh stack init <branch-name>` to start a stack and `gh stack add -m "message" <branch-name>` for each layer on top. Use `git checkout -b branch-name` for standalone work or as the fallback.
- Never push or force-push to `main` or trunk directly. Pushing feature/stacked branches and submitting PRs (`git push`, `gh stack submit`) is fine and does not require asking first.
- Always sync trunk before starting new work: `gh stack sync` when inside a stack, otherwise `git fetch origin && git checkout main && git pull --rebase`.

## Stacked Pull Requests

Stacking is native to GitHub via the `gh stack` extension (public preview). Install it once with
`gh extension install github/gh-stack`.

- Before using `gh stack`, check that the extension is installed: `gh extension list | grep -q gh-stack`.
- Stacking is enabled per repository. If a `gh stack` command exits with code `9`, stacked pull
  requests are not enabled for that repo — say so and use the plain-`git` fallback instead.
- Core commands:
  - `gh stack init <branch>` - start a stack off trunk. Also adopts existing branches: `gh stack init <branch-a> <branch-b>`.
  - `gh stack add -m "message" <branch>` - commit current work and add the next layer. Must be run from the topmost branch of the stack.
  - `gh stack view` - show the stack, its ordering, and PR links (`-s` for short, `--json` for machine-readable).
  - `gh stack submit --open` - push every branch and create or update the PRs.
  - `gh stack sync` - fetch, cascade-rebase, push, and reconcile PR state (`--prune` also deletes local branches for merged PRs).
  - `gh stack rebase` - cascade-rebase after trunk moves (`--upstack` / `--downstack` to limit scope).
  - `gh stack merge <pr>` - merge every PR up to and including that one, all or nothing.
  - `gh stack up` / `down` / `top` / `bottom` / `trunk` / `checkout` - navigate the stack.
  - `gh stack link <branch-or-pr> <branch-or-pr> ...` - stack already-pushed branches on GitHub, bottom to top, without local tracking.
- Gotchas worth remembering:
  - `gh stack submit` creates **draft** PRs by default. Pass `--open` to mark them ready for review.
  - `gh stack modify` is the interactive **restructure** UI (drop, fold, reorder, rename) — it is not an amend.
    To amend the current branch, run `git commit --amend` and then `gh stack rebase --upstack`.
  - `gh stack modify` requires a clean working tree, a linear history, and no rebase in progress.
  - `gh stack init` turns on `git rerere`, so a conflict resolved once is replayed on later branches in the stack.
- Fallbacks when stacking is unavailable:
  - branch creation -> `git checkout -b branch-name`
  - stack view -> `git log --oneline --graph --decorate --all -20`
  - submit -> `gh pr create --base <parent-branch>` per branch, in stack order
  - sync / rebase -> `git fetch origin` plus a manual rebase per child branch
  - amend -> `git commit --amend`, then rebase each downstream branch by hand
- When falling back, say explicitly that downstream branches will not be rebased automatically and
  that the PRs will not be linked as a stack on GitHub.

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
- When amending a branch mid-stack, run `git commit --amend` and then `gh stack rebase --upstack` so the layers above pick the change up.
- If a rebase hits conflicts, stop and show the conflicts instead of guessing through them.

## Commits

- Use Conventional Commits: `feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:`, `perf:`, `ci:`, `build:`.
- Keep subjects concise and under 72 characters.
- Use the body for why, not what.
- Never add `Co-Authored-By` trailers.

## Testing

- Before committing, run tests related to the changed files only.
- If the related test surface is unclear, stop and ask rather than running the whole suite by default.
- When fixing a bug, write a failing test that reproduces it before writing the fix, and keep it as the regression test.
- New behavior ships with tests in the same branch as the change.

## Active Task Convention

Per-task working memory lives at `$(git rev-parse --show-toplevel)/.local/active/<slug>/`. Each task has four files:

- `spec.md` - the what and why: goal, scope (in / out), success criteria, and open questions. Agreed with the human before any planning or implementation.
- `plan.md` - the how: the implementation steps or PR decomposition derived from the approved spec.
- `notes.md` - running log plus status frontmatter
- `review.md` - pre-merge findings and hardening notes

`notes.md` frontmatter is the workflow source of truth:

```markdown
---
slug: YYYY-MM-DD-<kebab>
ticket: <link-or-id-or-empty>
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
- These paths override the default output locations of any planning workflow or plan mode. Do not save task specs or plans to `docs/`, `docs/plans/`, `../<repo>_plans/`, or any other external or repo-tracked location while the task is active.
- If `.local/active/` is empty, start the task first before writing a spec or plan.
- Draft plans with the tool's native plan mode (Claude Code Plan Mode, Codex plan mode, OpenCode's plan agent). When the human approves a plan, save it to the current task's `plan.md` before implementing.

## Tickets And Specs

- A ticket link or ID in the `ticket:` frontmatter can point at any tracker (Linear, GitHub Issues, or other). Never hardcode workflow behavior to one tracker.
- The ticket owns the problem statement; `spec.md` owns the agreed solution. Link to the ticket rather than copying it.
- When a task starts from a ticket, fetch it once into `spec.md`'s Goal section — a short summary plus a source line (`Fetched from <link> on <date>`) — using whatever access the session has (MCP tool, `gh issue view`, or ask the user to paste it). Then record only the delta the ticket lacks: scope in/out, success criteria, chosen approach.
- If the ticket changes mid-task, the local spec wins until a human re-syncs it deliberately.

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
