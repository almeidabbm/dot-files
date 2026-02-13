---
name: worktree-setup
description: Set up a git worktree and do work in it, then clean up when done
user_invocable: true
---

# Worktree Workflow

Full end-to-end workflow: create worktree, do the work, and clean up.

## 1. Setup

- Run `gt sync` to ensure trunk is up to date.
- Run `git worktree list` to check existing worktrees.
- Identify the repo name from the current directory.
- Create the worktree from trunk as a sibling directory:
    - `git worktree add ../<repo-name>-<feature> trunk`
    - Example: `git worktree add ../lightdash-fix-auth main`
- `cd` into the worktree directory.
- Build branches/stacks inside the worktree from here.

## 2. Do the work

- Work entirely inside the worktree directory.
- Use all tools as normal (read, edit, write, run tests, etc.).
- For larger features, **build a Graphite stack** within the worktree:
    - Plan the decomposition upfront and present it to the user before starting.
    - Use `gt create -m "<step-name>"` for each logical step.
    - Each stacked branch must be independently reviewable, not break the build, and introduce minimal changes.
    - Run related tests before creating the next branch in the stack.
    - Use `gt log` to verify the stack structure as you go.
- For small changes, a single `gt create -m "<branch-name>"` with one commit is fine.
- Commit following conventional commits format.

## 3. Wrap up

Once the work is complete and the user is satisfied:

- Ask the user: **"Should I submit this stack with Graphite (`gt submit --stack`), push with git, or will you handle it yourself?"**
    - If Graphite submit: run `gt submit --stack`.
    - If git push: run `git push -u origin <branch-name>`.
    - If the user will handle it: wait for them to confirm they've pushed/submitted before proceeding to cleanup.
- After the push/submit is confirmed:
    - `cd` back to the original working directory.
    - Run `git worktree remove ../<repo-name>-<feature>`.
    - Confirm cleanup is done.
