---
name: start-task
description: Use when starting new work such as a feature, bugfix, refactor, investigation, or planning task; when the user mentions a ticket link or issue ID; or when they say they want to begin working on something. Creates a task in central agent memory with templated files and a detected size.
---

# Start Task

Create a task through `agent-memory`. The CLI owns stable identity, central
storage, repository bindings, and templates; do not hand-create a
repository-local `.local` folder.

This skill only sets up the task. Do not automatically design or implement it
unless the user also asks for that work.

## 1. Check the runtime

1. Resolve the repository root with `git rev-parse --show-toplevel`.
2. Require `agent-memory` on `PATH`. If it is missing, tell the user to run the
   relevant dot-files link script; do not silently fall back to a new `.local`.
3. Resolve the memory root with `agent-memory root --repo <repo-root>`.

## 2. Determine and confirm the slug

Use `YYYY-MM-DD-<kebab-feature-name>`. Planning-only tasks use
`YYYY-MM-DD-plan-<project-name>`.

Resolution order:

1. If the user gives a task name, turn it into a slug.
2. If a ticket title is available, propose a slug based on it.
3. If the task is still unclear, ask one concise question before creating it.

Always confirm the slug before creating the task.

## 3. Ingest a ticket once

If the user gave a ticket link or ID from any tracker:

1. Fetch it using the available tracker access.
2. After task creation, summarize the problem into `spec.md`'s Goal with
   `Fetched from <link> on <date>`.
3. Do not copy the ticket. The ticket owns the problem; the spec owns the
   agreed solution and records scope, success criteria, chosen approach, and
   missing decisions.
4. For a quick task, a link and one-line goal are enough.

If the ticket cannot be fetched, retain the reference and continue.

## 4. Detect task size

Default to `standard`.

Use `quick` for tiny copy, lint, rename, revert, or hotfix work. Use `big` for a
migration, architecture change, redesign, rewrite, scaffold, spike, planning
project, or work touching warnings found under the path returned by
`agent-memory system-map --repo <repo-root>`.

Always tell the user when `quick` or `big` is selected and why.

## 5. Verify repository hygiene

Check `.gitignore` for `.worktrees/` and the legacy `.local/` exclusion. Offer
to add missing entries. The latter protects retained migration sources; new
tasks do not live there.

## 6. Create and bind the task

Run:

```text
agent-memory create --slug <slug> --title <title> --ticket <ticket-or-empty> --size <size> --repo <repo-root> --role primary
```

The printed directory contains `task.json`, `spec.md`, `plan.md`, `notes.md`,
and `review.md`. Use that exact path for subsequent edits.

If the task already spans other repositories, attach each explicitly:

```text
agent-memory add-repo <task-id-or-slug> --repo <checkout> --role <role>
```

Never infer that two tasks are identical merely because they share a ticket.

## 7. Confirm and suggest next steps

Show the task path, stable task ID, repositories, detected size, current
status, and likely next move. Mention other active tasks only when helpful;
never choose a current task by modification time.

Suggested moves:

- design the approved solution in `spec.md`
- draft the implementation plan in the tool's native plan mode, then save the
  human-approved plan to `plan.md`

## Edge cases

- If the slug exists, ask whether to resume it or choose another.
- If a repository has several active tasks, bind the intended one explicitly.
- Keep machine paths, private ticket references, task contents, and migration
  reports in central memory; do not post them publicly.
