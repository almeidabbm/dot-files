---
name: start-task
description: Use when starting new work such as a feature, bugfix, refactor, investigation, or planning task; when the user mentions a ticket link or issue ID; or when they say they want to begin working on something. Creates .local/active/<slug>/ with templated task files and a detected size.
---

# Start Task

Create the per-task working-memory folder under `.local/active/<slug>/` with four files: `spec.md`, `plan.md`, `notes.md`, and `review.md`.

This skill only sets up the task folder. Do not automatically start design or implementation work unless the user asks for it next.

> The shared workflow rules (your global agent rules) are the source of truth for the `.local/active/` layout and the `notes.md` frontmatter schema. The templates below implement that convention; if the two ever disagree, follow the shared rules.

## 1. Determine the slug

Use `YYYY-MM-DD-<kebab-feature-name>`. Planning-only tasks use `YYYY-MM-DD-plan-<project-name>`.

Resolution order:

1. If the user gives a task name, turn it into a slug.
2. If a ticket title is available, propose a slug based on it.
3. If the task is still unclear, ask one concise question before creating anything.

Always confirm the slug before creating the folder.

## 1b. Ingest the ticket, if one was provided

If the user gave a ticket link or ID (any tracker — Linear, GitHub Issues, or other):

1. Fetch it once, using whatever access this session has: an MCP tool, `gh issue view`, or ask the user to paste the content.
2. Summarize the problem statement into `spec.md`'s Goal section, with a source line: `Fetched from <link> on <date>`.
3. Do not copy the full ticket. The ticket owns the problem statement; `spec.md` records the link plus the delta it lacks — scope (in / out), success criteria, chosen approach. List missing pieces under Open questions.
4. For `quick` tasks, the ticket link plus a one-line goal is enough.

If the ticket cannot be fetched, record the link anyway and continue; the spec design step fills the gaps with the user.

## 2. Detect task size

Default to `standard`, then adjust based on signals.

Use `quick` when any of these are true:

- The task sounds like a typo, rename, copy tweak, lint fix, revert, or tiny hotfix.
- The request is extremely short or obviously narrow.

Use `big` when any of these are true:

- The task is a migration, refactor, redesign, rewrite, architecture change, scaffold, or spike.
- The slug starts with `plan-`.
- The task is likely to touch areas already called out in `.local/system-map/danger-*.md`.

Always show the user the detected size and the signals that led to it. Do not silently choose `quick` or `big`.

## 3. Verify gitignore

Resolve the repo root with `git rev-parse --show-toplevel`. Check `.gitignore` for:

```gitignore
.local/
.worktrees/
```

If either entry is missing, offer to add it before continuing.

## 4. Create the folder and templates

Create:

- `.local/active/<slug>/spec.md`
- `.local/active/<slug>/plan.md`
- `.local/active/<slug>/notes.md`
- `.local/active/<slug>/review.md`

Use these contents.

### `spec.md`

```markdown
# <Task title>

**Status:** spec
**Created:** YYYY-MM-DD
**Ticket:** <link-or-empty>

## Goal
_To be defined during design._

## Scope (in / out)

## Success criteria

## Open questions
```

### `plan.md`

```markdown
# plan.md

_To be populated once the spec is clear and approved._
```

### `notes.md`

```markdown
---
slug: <slug>
ticket: <link-or-id-or-empty>
size: <detected-size>
status: spec
last-updated: <ISO timestamp>
---

## Open questions

## Log

- <ISO timestamp> - created via start-task
```

### `review.md`

```markdown
_Populated by pre-merge. Do not edit by hand._
```

## 5. Confirm and suggest next steps

Show:

- the folder that was created
- the detected size
- the current status
- the next likely move

Suggested next moves:

- design the spec in `spec.md` - interview the user about goal, scope (in / out), and success criteria before proposing a design
- write the implementation plan in `plan.md` - use the tool's native plan mode to explore, then save the approved plan there

## Edge cases

- If the slug already exists, ask whether to resume it or pick a different slug.
- If there are already multiple active tasks, that is fine; mention the most recent one so the user sees existing context.
- If the repo has no `.gitignore`, create it if the user approves.
