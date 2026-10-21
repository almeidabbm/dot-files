---
name: lightdash-stack
description: Use in a repo that has a `rainbow.toml` (lightdash) whenever the running app is needed: to run, preview, screenshot, browser-test or e2e a branch, or to start a dev stack in a worktree. Decides between a Rainbow cloud environment and the local pm2 stack, and gives the Rainbow recipe.
---

# lightdash-stack — Rainbow or local?

The laptop holds one stack: `lightdash-*` on `main`, under pm2. Every other branch runs in Rainbow. A worktree never gets its own pm2 stack; a second local stack plus a typecheck is what swaps the machine.

## Decide

Rainbow, when any of these hold:

- The branch lives in a worktree.
- The goal is to see, screenshot, browser-test or e2e the change.
- A PR is open: its `lightdash--pr-<number>` env already exists.
- Someone else should open it.

Local `main` stack, only when:

- A debugger must attach, or Maple traces are the point (`debug-local`).
- The loop is edit-and-look in seconds and a push per iteration is too slow. Do that on `main`, or accept the push.

Typechecks and unit tests stay local either way. Run them one at a time across sessions; each full typecheck peaks near 2.5 GB.

## Rainbow recipe

1. Commit and push the branch. Rainbow serves pushed commits only.
2. `create_env` with the branch name. Reuse the same `name` to update in place at the same URL. Source-only diffs fork the warm parent in about 100 ms; a change under `packages/common`, `warehouses`, migrations or controllers triggers that tier's rebuild first.
3. Drive the URL with the browser. Demo login is `demo@lightdash.com` / `demo_password!`, seeded with the Jaffle shop project. Envs run in PR mode: email passcode is `000000`, the feature-flag management API is on.
4. `verify` runs readiness, warm routes and first paint, plus an optional guest command. `exec` runs anything in the guest; the repo is at `/usr/app`, with `packages/api-tests` and Playwright with Chromium available.
5. Re-push to update. Once the PR opens, switch to its `lightdash--pr-<number>` env and let the branch env hibernate. Hibernated envs wake on the next request to their URL.

Caveats: integrations (Ask AI, data apps, GitHub) work only where the platform holds the secret, and egress is closed to hosts outside `rainbow.toml`'s allowlist. `verify` reports blocked hosts with the TOML that would admit them.

## Local hygiene

- Before starting a worktree stack for any reason, stop it again as soon as the check is done: `./node_modules/.bin/pm2 stop /^<id>-/`.
- One stack up means six tsc watchers fewer. Check with `./node_modules/.bin/pm2 list`.
