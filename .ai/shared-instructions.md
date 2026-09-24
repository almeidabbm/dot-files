# Shared AI Workflow Rules

Personal defaults across agent tools. The user's current instructions, the host's permissions, and the repository's own rules take precedence.

## Task And Context

- Keep one conversation per coherent task. Continue related follow-ups in that conversation; start a fresh session for unrelated work.
- Read the relevant code, repository instructions, and existing tests before changing behavior. Search for specific files and symbols rather than loading the whole repository.
- Identify the intended outcome, constraints, and the evidence that will establish completion. Resolve material ambiguity with the user; make routine implementation choices autonomously.
- If the change is not a one-sentence diff, state a plan before implementing. Scale the plan to the work.
- Keep durable scope and decisions in the ticket or PR when one exists. Before compaction or handoff, preserve the goal, decisions, remaining work, and verification status.

## Delegation

- You own the task, integration, and final result. Default to working locally. Delegate only when an independent subtask can run alongside useful local work and the expected benefit exceeds briefing, coordination, and verification costs. Keep a bug's reproduction and root-cause investigation together.
- Worker roles are `investigator` (read-only evidence gathering), `implementer` (a specified change with tests in an assigned scope), and `reviewer` (independent, evidence-backed review of a diff). Choose the role that fits the delegated subtask.
- Load the `delegation` skill when you delegate: it covers provider, model, and effort selection, route commands, the brief template, and result verification.
- If you are a worker, complete the brief and return evidence to the parent. Leave further delegation and Git coordination to the parent unless the brief assigns them.

## Git And Delivery

- Load the `git-workflow` skill before starting implementation and before the first branch, commit, stack, worktree, or PR operation in a task. It owns trunk sync, `gh stack`, its fallbacks, and worktree conventions.
- Follow the repository's branch policy; preserve existing user changes.
- Pushing feature branches and submitting PRs within the task is authorized without asking again.
- Use Conventional Commits with subjects under 72 characters. Use the body for why. Never add `Co-Authored-By` trailers.
- If a rebase conflicts, stop and show the conflicts instead of guessing through them.

## Verification

- When fixing a bug, first write a failing test that reproduces it, then keep that test with the fix. New behavior ships with tests in the same branch.
- Run checks related to the changed files before committing or reporting completion. Find the commands in repository instructions, scripts, or CI. If the related test surface remains unclear, ask rather than running the whole suite by default.
- For documentation-only changes, verify referenced files, links, and command examples. For UI behavior, inspect the running result when the necessary tools are available.
- Review the final diff against the request for correctness, regressions, and unrelated changes. Validate worker findings and test evidence; a success message alone is insufficient.
- Report what changed, what was verified, and what remains unverified or blocked. Distinguish checks actually run from suggested checks.

## Scope And Style

- The ticket, when present, owns the problem statement and status. For larger work, record agreed scope, success criteria, and approach in the ticket or PR before implementing.
- Prefer open PRs and tracker status as the handoff surface across sessions. Keep the workflow independent of any particular tracker.
- Follow existing project conventions and patterns; prefer functional patterns where appropriate.
- Keep changes focused. Avoid unnecessary annotations, comments, or docstrings in code you did not change.
- Improve shared instructions after observed, recurring friction. Keep always-relevant rules in this file, occasional procedures in the `git-workflow` and `delegation` skills, worker roles in the agent definitions, and repository-specific facts in that repository. Remove obsolete or conflicting guidance rather than accumulating exceptions.
