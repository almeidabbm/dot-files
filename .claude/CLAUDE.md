# Global Claude Code Rules

## Git & Branching

- Use **Graphite CLI (`gt`)** for branch management instead of raw git commands when possible.
- Use `gt create -m "branch-name"` to create branches (stacked on current branch).
- Use plain `git checkout -b` only for independent branches that are NOT part of a stack.
- Never push or submit (`gt submit`) without explicit permission. Only create commits locally.
- Use `gt log` to visualize the current stack before making branching decisions.
- Always run `gt sync` before starting any new work to ensure trunk is up to date.

## Worktrees

- Store all worktrees in a single folder one level up: `../<repo-name>_worktrees/<feature>/`
    - Example: if repo is `~/Develop/lightdash`, worktrees go in `~/Develop/lightdash_worktrees/fix-auth`
- Create from trunk: `git worktree add ../<repo-name>_worktrees/<feature> trunk`
- Use Graphite (`gt create`, `gt log`, etc.) inside the worktree for branching and stacking.
- Run `docker compose` from inside the worktree directory (compose files use relative paths).
- Remind me to clean up worktrees when work is done (`git worktree remove`).

## Stacking Work

When implementing a feature or larger change, **break it into a stack of small, independent PRs** using Graphite:

- Each branch in the stack should be **reviewable on its own** - it must not break the code.
- Each branch should introduce **minimal, focused changes** (e.g., types first, then logic, then tests, then UI).
- Use `gt create -m "<branch-name>"` to stack each step on top of the previous one.
- Use `gt log` to verify the stack looks correct.
- A good decomposition example for a feature:
    1. `feat/add-types` - Add new types/interfaces
    2. `feat/add-backend-logic` - Implement backend/service logic
    3. `feat/add-tests` - Add tests
    4. `feat/add-api-endpoint` - Wire up the API and add tests for it
    5. `feat/add-frontend` - Add UI components
- Before creating each stacked branch, commit the current work and verify it doesn't break anything by running related tests.
- Present the planned stack decomposition to the user before starting, so they can adjust the scope of each PR.

## Modifying Stacked Branches

- When amending a branch mid-stack (e.g., after review feedback), use `gt modify` instead of raw git amend.
- After `gt modify`, always run `gt restack` to rebase all branches above.
- If `gt restack` hits merge conflicts, **stop and show me the conflicts** before attempting to resolve them.

## Commits

- Use **Conventional Commits** format: `feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:`, `perf:`, `ci:`, `build:`.
- Keep commit messages concise (subject line under 72 chars).
- Use the commit body for "why", not "what".
- Each commit within a stacked branch should also be self-contained and not break the build.

## Testing

- Before committing, run tests **related to the changed files only** (not the full suite).
- If unsure which tests are related, ask me rather than running the entire suite.

## Permissions

- When I approve a Bash command that isn't in the allow list, and it's a **local-only** operation (not push/submit), ask me if I want to add it to `~/.claude/settings.local.json` so it's auto-allowed next time.
- Never auto-add remote/destructive commands (`git push`, `gt submit`, `rm -rf`, etc.) without asking.

## Code Style (TypeScript / Node.js)

- Follow existing project conventions and patterns.
- Prefer functional patterns where appropriate.
- Do not add unnecessary type annotations, comments, or docstrings to code you didn't change.
- Keep changes minimal and focused on the task at hand.
