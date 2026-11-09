---
name: dev-stack
description: "Use whenever the running app is needed: to run, preview, screenshot, browser-test or e2e a branch, or to start a dev stack in a worktree. Decides between a remote preview environment and the one local stack."
---

# dev-stack: remote or local?

The laptop holds one local stack, on the default branch. Every other branch runs in a remote preview environment. A worktree never gets its own local stack; a second stack plus a typecheck is what swaps the machine.

## Repo specifics first

Read `$(git rev-parse --path-format=absolute --git-common-dir)/../.local/runtime/stack.md`. It names the remote provider, its recipe, logins and the local stack's commands, and it overrides the defaults below. When it is missing, ask which remote environment the repo uses before starting anything local.

## Decide

Remote, when any of these hold:

- The branch lives in a worktree.
- The goal is to see, screenshot, browser-test or e2e the change.
- A PR is open and its preview environment already exists.
- Someone else should open it.

Local default-branch stack, only when:

- A debugger must attach, or local tracing is the point.
- The loop is edit-and-look in seconds and a push per iteration is too slow. Do that on the default branch, or accept the push.

Typechecks and unit tests stay local either way. Run them one at a time across sessions.

## Hand back

End every build the user should try with a link to an environment you started yourself, with the feature flag on when the change sits behind one, and the two or three things to check there. Never change flags on shared or CI environments.

## Local hygiene

Stop any extra local stack as soon as its check is done, and confirm only one stack runs.
