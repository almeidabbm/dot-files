# Shared AI Workflow Rules

## Git & Branching

- Use GitHub's native stacked pull requests (`gh stack`) for branch management whenever the repo supports it; fall back to plain `git` plus `gh pr` when it does not.
- Use `gh stack init <branch-name>` to start a stack and `gh stack add -m "message" <branch-name>` for each layer on top. Use `git checkout -b branch-name` for standalone work or as the fallback.
- Pushing feature and stacked branches and submitting PRs (`git push`, `gh stack submit`) is fine and does not require asking first.
- Keep the stack rebased on current trunk: before starting new work, and again whenever trunk moves. Use `gh stack sync` inside a stack, otherwise `git fetch origin` and rebase the branch onto `origin/<trunk>`.
- Each repository owns its own branch policy. Follow the rules the repository states — in its `AGENTS.md`/`CLAUDE.md`, its branch protection, or its CI — rather than assuming a policy it has not written down.

## Stacked Pull Requests

Stacking is native to GitHub via the `gh stack` extension (public preview). Install it once with
`gh extension install github/gh-stack`.

- Before using `gh stack`, check that the extension is installed: `gh extension list | grep -q gh-stack`.
- Stacking is enabled per repository. If a `gh stack` command exits with code `9`, stacked pull
  requests are not enabled for that repo — say so and use the plain-`git` fallback instead.
- Run `gh stack --help` (or `gh stack <command> --help`) for the command set rather than guessing at it.
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
- Copy `.env*` and `.envrc` from the main repo into the worktree, ignoring missing files.
- Run `docker compose` from inside the worktree directory when compose files use relative paths.
- Remind the user to clean up finished worktrees with `git worktree remove .worktrees/<feature>`.

## Sessions

- One task per conversation. Start a fresh session between unrelated tasks.
- If the change is not a one-sentence diff, plan (or stack-decompose) before implementing.

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

## Tickets And Scope

- The ticket (Linear, GitHub Issues, or other) owns the problem statement and status.
- For larger work, record agreed scope, success criteria, and chosen approach in the ticket or PR description before implementing.
- Prefer open PRs and tracker status as the handoff surface across sessions.
- Never hardcode workflow behavior to one tracker.

## Per-Repo Gitignore

Every repo using worktrees should gitignore them (and any leftover legacy local memory dirs):

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
