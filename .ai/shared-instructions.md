# Shared AI Workflow Rules

These are personal defaults across agent tools. Follow the user's current instructions, the host's permissions, and the repository's applicable rules. Resolve the supporting files named below under `~/Develop/dot-files/.ai/`, including when this file is loaded through a symlink.

## Task And Context

- Keep one conversation per coherent task. Continue related follow-ups in that conversation; start a fresh session for unrelated work.
- Read the relevant code, repository instructions, and existing tests before changing behavior. Search for specific files and symbols rather than loading the whole repository.
- Identify the intended outcome, constraints, and evidence that will establish completion. Resolve material ambiguity with the user; make routine implementation choices autonomously.
- If the change is not a one-sentence diff, state a plan before implementing. Scale the plan to the work; a short explanation is enough for a small change.
- Keep durable scope and decisions in the ticket or PR when one exists. Before compaction or handoff, preserve the current goal, decisions, remaining work, and verification status in the session summary or existing handoff surface.

## Delegation

- The agent talking to the user owns the task, integration, and final result. Handle small or tightly coupled work directly.
- Delegate bounded research, specification, implementation, or review when independent work, a focused context, or specialist capability would improve the outcome enough to justify the handoff. Delegation within the authorized task does not require separate confirmation.
- Before spawning a worker, read `~/Develop/dot-files/.ai/delegation.md` and `~/Develop/dot-files/.ai/models.md`. Choose the worker's model and execution tool for its assignment.
- If you were assigned a worker role, complete that brief and return evidence to the parent. Leave further delegation and Git coordination to the parent unless the brief explicitly assigns them.

## Git And Delivery

- Before starting implementation or creating/updating branches, stacks, worktrees, commits, or PRs, read `~/Develop/dot-files/.ai/git-workflow.md`. It owns the Git commands, sync procedure, stacking fallbacks, and worktree conventions.
- Use `gh stack` where the repository supports it. Follow the repository's branch policy; preserve existing user changes.
- Pushing feature branches and submitting PRs within the task is authorized without asking again.
- Use Conventional Commits with subjects under 72 characters. Use the body for why. Never add `Co-Authored-By` trailers.
- If a rebase conflicts, stop and show the conflicts instead of guessing through them.

## Verification

- When fixing a bug, first write a failing test that reproduces it, then keep that test with the fix. New behavior ships with tests in the same branch.
- Run checks related to the changed files before committing or reporting completion. Find the relevant commands in repository instructions, scripts, or CI. If the related test surface remains unclear, ask rather than running the whole suite by default.
- For documentation-only changes, verify referenced files, links, and command examples. For UI behavior, inspect the running result when the necessary tools are available.
- Review the final diff against the request for correctness, regressions, and unrelated changes. Validate worker findings and test evidence; a success message alone is insufficient.
- Report what changed, what was verified, and what remains unverified or blocked. Distinguish checks actually run from suggested checks.

## Scope And Style

- The ticket, when present, owns the problem statement and status. For larger work, record agreed scope, success criteria, and approach in the ticket or PR before implementing.
- Prefer open PRs and tracker status as the handoff surface across sessions. Keep the workflow independent of any particular tracker.
- Follow existing project conventions and patterns; prefer functional patterns where appropriate.
- Keep changes focused. Avoid unnecessary annotations, comments, or docstrings in code you did not change.
- Improve shared instructions after observed, recurring friction. Keep generally useful rules here, occasional procedures in referenced files, and repository-specific facts in that repository. Remove obsolete or conflicting guidance rather than accumulating exceptions.
