# Global Claude Code Rules

## Git & Branching

- **Never commit directly to `main` (or trunk).** Before making any commits, check the current branch with `git branch --show-current`. If on `main`, create a new branch first.
- Prefer **Graphite CLI (`gt`)** for branch management when available; fall back to plain `git` when it isn't (see "Graphite Availability" below).
- `gt create -m "branch-name"` to create branches stacked on the current one; plain `git checkout -b branch-name` is the fallback or for independent (non-stacked) branches.
- **Never push or submit** (`git push`, `gt submit`) **without explicit permission.** Only create commits locally.
- Always sync trunk before starting new work: `gt sync` if available, otherwise `git fetch origin && git checkout main && git pull --rebase`.

## Graphite Availability

Graphite (`gt`) is the preferred branch-management CLI, but it may not be installed on every machine.

- Before running any `gt` command, check `command -v gt` and fall back to plain `git` if missing.
- Fallbacks:
    - `gt sync` → `git fetch origin && git checkout main && git pull --rebase`
    - `gt create -m "branch-name"` → `git checkout -b branch-name`
    - `gt log` → `git log --oneline --graph --decorate --all -20`
    - `gt modify` → `git commit --amend` (no automatic restack of downstream branches)
    - `gt restack` → manual rebase per child branch
    - `gt submit` still requires explicit permission per the never-push-without-permission rule.
- When `gt` is missing, mention to the user that stacked-PR tooling won't auto-restack — they may need to rebase manually.

## Worktrees

- Worktrees live **inside the repo** at `$(git rev-parse --show-toplevel)/.worktrees/<feature>/` (gitignored).
- Create from trunk: `git worktree add .worktrees/<feature> trunk`.
- After creating a worktree, **symlink `.local`** so the worktree shares project intel with the main repo:
    ```
    ln -s ../.local .worktrees/<feature>/.local
    ```
- Copy `.env*` and `.envrc` from the main repo into the worktree:
    ```
    cp <main-repo>/.env* <main-repo>/.envrc .worktrees/<feature>/
    ```
    (Ignore errors if `.envrc` doesn't exist.)
- Run `docker compose` from inside the worktree directory (compose files use relative paths).
- Remind the user to clean up worktrees when work is done: `git worktree remove .worktrees/<feature>`.

## Stacking Work

When implementing a feature or larger change, **break it into a stack of small, independent PRs**:

- Each branch in the stack should be **reviewable on its own** — it must not break the code.
- Each branch should introduce **minimal, focused changes** (e.g., types first, then logic, then tests, then UI).
- Use `gt create -m "<branch-name>"` to stack on top of the previous branch when `gt` is available.
- Use `gt log` (or `git log --oneline --graph --decorate --all`) to verify the stack looks correct.
- A good decomposition example for a feature:
    1. `feat/add-types` — Add new types/interfaces
    2. `feat/add-backend-logic` — Implement backend/service logic
    3. `feat/add-tests` — Add tests
    4. `feat/add-api-endpoint` — Wire up the API and add tests for it
    5. `feat/add-frontend` — Add UI components
- Before creating each stacked branch, commit the current work and verify it doesn't break anything by running related tests.
- Present the planned stack decomposition to the user before starting, so they can adjust the scope of each PR.

## Modifying Stacked Branches

- When amending a branch mid-stack (e.g., after review feedback), use `gt modify` if available; otherwise `git commit --amend` and manually rebase downstream branches.
- After `gt modify`, always run `gt restack` to rebase all branches above.
- If `gt restack` hits merge conflicts, **stop and show the user the conflicts** before attempting to resolve them.
- When `gt` is missing, walk each child branch and `git rebase` it onto the updated parent — flag this to the user.

## Commits

- Use **Conventional Commits** format: `feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:`, `perf:`, `ci:`, `build:`.
- Keep commit messages concise (subject line under 72 chars).
- Use the commit body for "why", not "what".
- Each commit within a stacked branch should also be self-contained and not break the build.
- **Never** add `Co-Authored-By` or any co-author trailer to commit messages. All commits should appear as authored solely by the user.

## Testing

- Before committing, run tests **related to the changed files only** (not the full suite).
- If unsure which tests are related, ask rather than running the entire suite.

## Permissions

- When the user approves a Bash command that isn't in the allow list, and it's a **local-only** operation (not push/submit), ask if they want to add it to `~/.claude/settings.local.json` so it's auto-allowed next time.
- Never auto-add remote/destructive commands (`git push`, `gt submit`, `rm -rf`, etc.) without asking.

## Active Task Convention

Per-task working memory lives at `$(git rev-parse --show-toplevel)/.local/active/<slug>/`. Each task has four files:

- `spec.md` — written by `superpowers:brainstorming` (the design).
- `plan.md` — written by `superpowers:writing-plans` (the stack decomposition).
- `notes.md` — running log + open questions + status front-matter.
- `review.md` — written by `/pre-merge` (adversarial findings + harden checklist).

**`notes.md` front-matter is the workflow source of truth:**

```markdown
---
slug: YYYY-MM-DD-<kebab>
linear: <issue-id-or-empty>
size: quick | standard | big
status: spec | plan | implementing | review | ready-to-ship | merged | archived
last-updated: <ISO timestamp>
---
```

Skills update `status` and `last-updated` as they progress. Do not edit by hand.

- **Current task** = the most recently modified folder under `.local/active/`. No pointer file.
- On archive, move `active/<slug>/` → `archive/<slug>/`.
- Durable architectural intelligence lives in `.local/system-map/` (prefixed filenames: `inv-`, `area-`, `danger-`, `pitfall-`).

## Workflow Auto-Prompts

Proactively suggest the right command at the right moment — the user does not memorize skill names.

- User mentions a Linear issue ID, an issue title, or "starting work on X" AND no matching `.local/active/<slug>/` exists → suggest `/start-task`.
- User says they're done implementing, tests pass, or asks "ready to ship?" / "can we merge?" → suggest `/pre-merge`.
- `gh pr view --json state` shows the current branch's PR is `MERGED` → suggest `/archive-task`.
- User asks "where was I?" / "what was I working on?" / seems disoriented → run `/status`.

## Per-Repo Gitignore

Every repo using this workflow must gitignore the working-memory and worktree folders. Add these two lines to the repo's `.gitignore`:

```
.local/
.worktrees/
```

- **Do not** modify the global excludesfile (`~/.config/git/ignore`) for this — keep the rule explicit and version-controlled per repo.
- When starting work in a new repo for the first time, check its `.gitignore`. Some repos (e.g. lightdash) already cover `.local/*` and `.worktrees/`. Otherwise, propose adding the two lines as part of the first commit.

## Superpowers Skill Overrides

The following rules **override** any defaults from superpowers skills. These take priority over skill instructions.

### Branch Management (overrides `finishing-a-development-branch` skill)

- Use `gt create -m "<branch-name>"` instead of `git checkout -b` **when `gt` is available**; otherwise fall back to `git checkout -b` (see "Graphite Availability").
- Use `gt submit` (with permission) instead of `git push -u origin` when available; otherwise `git push` (still requires permission).
- Use `gt log` to show branch state when available; otherwise `git log --oneline --graph --decorate --all -20`.
- For PRs, prefer `gt submit` + Graphite PR workflow when available; otherwise `gh pr create`.

### Plan Files (overrides `writing-plans` skill)

- Plans for the current task are written to `$(git rev-parse --show-toplevel)/.local/active/<current-slug>/plan.md`.
- The "current slug" is the most recently modified folder under `.local/active/`.
- If `.local/active/` is empty, prompt the user to run `/start-task` first.
- **Do NOT** save plans to `docs/plans/`, `../<repo>_plans/`, or any other external folder.

### Spec Files (overrides `brainstorming` skill)

- Specs for the current task are written to `$(git rev-parse --show-toplevel)/.local/active/<current-slug>/spec.md`.
- The "current slug" is the most recently modified folder under `.local/active/`.
- If `.local/active/` is empty, prompt the user to run `/start-task` first.
- **Do NOT** save specs to `docs/superpowers/specs/` or any other repo-tracked location.
- Specs may later be graduated to a committed `docs/architecture/<feature>.md` via `/archive-task`.

## Code Style (TypeScript / Node.js)

- Follow existing project conventions and patterns.
- Prefer functional patterns where appropriate.
- Do not add unnecessary type annotations, comments, or docstrings to code you didn't change.
- Keep changes minimal and focused on the task at hand.
