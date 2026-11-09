# Shared AI Workflow Rules

Personal defaults across agent tools. The user's current instructions, the host's permissions, and the repository's own rules take precedence.

## Task And Context

- Keep one conversation per coherent task. Continue related follow-ups in that conversation; start a fresh session for unrelated work.
- Read the relevant code, repository instructions, and existing tests before changing behavior. Search for specific files and symbols rather than loading the whole repository.
- Identify the intended outcome, constraints, and the evidence that will establish completion. Resolve material ambiguity with the user; make routine implementation choices autonomously.
- If the change is not a one-sentence diff, state a plan before implementing. Scale the plan to the work.
- Keep durable scope, decisions, and in-flight work in the project's private state file (`project-state` skill). Before compaction or handoff, update it with the goal, decisions, remaining work, and verification status.
- Ask the user before deciding anything hard to undo: data shape, file and as-code formats, permissions and security, endpoints and contracts, migrations and persistence, behavior with a feature flag off, and which existing behavior the change touches. Changes add or fix; break existing behavior only when nothing else works, and say so first. Decide easy-to-undo details yourself (UI polish behind a flag, wording, spacing) and list them for the user's batched review.

## Delegation

- You own the task, integration, and final result. Default to working locally. Delegate only when an independent subtask can run alongside useful local work and the expected benefit exceeds briefing, coordination, and verification costs. Keep a bug's reproduction and root-cause investigation together.
- Use the host's built-in subagents: a read-only explorer for investigation, a general agent for implementation, and a fresh-context read-only review before a PR, aimed at the PR's risk map.
- Load the `delegate` skill when you delegate: it covers provider, model, and effort selection, route commands, the brief template, and result verification.
- If you are a worker, complete the brief and return evidence to the parent. Leave further delegation and Git coordination to the parent unless the brief assigns them.

## Git And Delivery

- Load the `git-workflow` skill before starting implementation and before the first branch, commit, worktree, or PR operation in a task. It owns trunk sync, layered commits, when to split PRs, the PR risk map, and worktree conventions.
- Follow the repository's branch policy; preserve existing user changes.
- Pushing feature branches and submitting PRs within the task is authorized without asking again.
- When the user says to merge, babysit, or ship a PR, load the `babysit-pr` skill: it waits for CI, handles review threads, and merges only when told to.
- Use Conventional Commits with subjects under 72 characters. Use the body for why. Never add `Co-Authored-By` trailers.
- If a rebase conflicts, stop and show the conflicts instead of guessing through them.

## Verification

- When fixing a bug, first write a failing test that reproduces it, then keep that test with the fix. New behavior ships with tests in the same branch.
- Run checks related to the changed files before committing or reporting completion. Find the commands in repository instructions, scripts, or CI. If the related test surface remains unclear, ask rather than running the whole suite by default.
- For documentation-only changes, verify referenced files, links, and command examples. For UI behavior, inspect the running result when the necessary tools are available.
- Spend review on blast radius: read the code of catastrophic layers (data, access, domain logic, contracts); check the rest against evidence such as tests, screenshots, or evals.
- Review the final diff against the request for correctness, regressions, and unrelated changes. Validate worker findings and test evidence; a success message alone is insufficient.
- Report what changed, what was verified, and what remains unverified or blocked. Distinguish checks actually run from suggested checks.

## Scope And Style

- The ticket, when present, owns the problem statement and status. For larger work, record agreed scope, success criteria, and approach in the project's state folder before implementing.
- Never name customers (people, companies, organizations, or identifying data) in tickets, issues, PRs, commits, or docs, internal tickets included; describe the use case generically. Treat tickets that sync to a public tracker and PRs in public repositories as public: the problem and acceptance criteria only, no internal reasoning, security detail, or working specs.
- Prefer the project's state file, open PRs, and tracker status as the handoff surface across sessions. Keep the workflow independent of any particular tracker.
- When reporting status or asking for a decision, use this shape: the current state in one line, what you need from the user, then the options with your recommendation first. Add detail only when asked.
- Write messages to the user so they read cold: name things by what they are, not by labels coined during the work, and state results instead of narrating upcoming steps. Working labels and running narration belong in agent-to-agent briefs and reports.
- In conversation with the user only, refer to tickets and PRs with descriptive Markdown links that say what changes. Shorten labels when context is established; include the affected feature in fresh mentions: `[PR adding chart images](url)` vs. `[PR adding chart images to Slack](url)`. Use natural wording, not exact titles or bare identifiers. This rule does not apply to authored artifacts such as PR descriptions, commit messages, or documentation.
- Follow existing project conventions and patterns; prefer functional patterns where appropriate.
- Keep changes focused. Avoid unnecessary annotations, comments, or docstrings in code you did not change.
- When the user corrects the same kind of thing a third time, add it to `delegate/review-standards.md` (code and review) or to this file (how you work), and tell the user what you added.
- Improve shared instructions after observed, recurring friction. Keep always-relevant rules in this file, occasional procedures in the `git-workflow` and `delegate` skills, and repository-specific facts in that repository. Remove obsolete or conflicting guidance rather than accumulating exceptions.
