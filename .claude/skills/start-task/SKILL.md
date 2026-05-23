---
name: start-task
description: Use when starting any new piece of work (feature, bugfix, refactor, investigation), when the user mentions a Linear issue ID, says "let's start on X", "begin work on Y", or wants to scope a new project. Creates .local/active/<slug>/ with templated files and auto-detected size.
---

# Start Task

## Overview

The on-ramp for any new piece of work. Creates the per-task folder under `.local/active/<slug>/` with four templated files (`spec.md`, `plan.md`, `notes.md`, `review.md`), auto-detects task size, and seeds `notes.md` front-matter as the workflow source of truth.

This skill does NOT chain into brainstorming or any other skill — it just sets up the folder. The user describes intent next; CLAUDE.md auto-prompts handle the nudging.

## 1. Determine the slug

**Slug format:** `YYYY-MM-DD-<kebab-feature-name>`. Planning tasks (no implementation) use `YYYY-MM-DD-plan-<project-name>`.

Resolution order:

1. **CLI argument given** — `/start-task add-dashboard-filters` → slug = `YYYY-MM-DD-add-dashboard-filters`.
2. **Linear MCP available + active/selected issue** — propose `YYYY-MM-DD-<kebab-of-issue-title>`. Show the user the proposed slug and let them adjust.
3. **No argument, no Linear context** — ask: "What's this task about? I'll turn your answer into a slug."

Always confirm the slug with the user before creating the folder.

## 2. Auto-detect size

Default size is `standard`. Bump up or down based on signals; **always disclose the reasoning** so the user can override.

### Bump to `quick` if ANY:

- Linear estimate ≤ 1 point, OR labels include `S`, `XS`, `quick`, `chore`, `hotfix`.
- Title matches `/\b(typo|rename|copy|tweak|hotfix|revert|bump|format|lint)\b/i`.
- Description empty or < ~100 chars.

### Bump to `big` if ANY:

- Linear estimate ≥ 5 points, OR labels include `L`, `XL`, `epic`, `project`.
- Linear issue has a parent project.
- Slug starts with `plan-`.
- Title matches `/\b(migrate|migration|refactor|redesign|rewrite|introduce|architect|scaffold|spike|tenancy|permissions|auth)\b/i`.
- Repo's `.local/system-map/danger-*.md` references areas the task is likely to touch.

### Disclose:

```
Detected size: big
Signals:
  • estimate: 8
  • label: "L"
  • title contains "migrate"

Confirm size? [Y/n/quick/standard/big]
```

Never silently pick `big` or `quick`. Always show the signals.

## 3. Verify gitignore

Resolve the repo root via `git rev-parse --show-toplevel`. Check the repo's `.gitignore` for `.local/` and `.worktrees/` entries.

If either is missing:

```
⚠ .local/ and .worktrees/ should be gitignored in this repo.
   Add them to .gitignore? (one-time setup per repo)
```

If user agrees, append the two entries to `.gitignore` and inform them to commit it as part of the first commit of this task.

## 4. Create the folder + templates

```
mkdir -p $(git rev-parse --show-toplevel)/.local/active/<slug>
```

Write four files:

### `spec.md`

```markdown
# <Task title>

**Status:** spec
**Created:** YYYY-MM-DD
**Linear:** <issue-id-or-empty>

## Goal
_To be populated by superpowers:brainstorming._

## Scope (in / out)

## Success criteria

## Open questions
```

### `plan.md`

```markdown
# plan.md

_To be populated by superpowers:writing-plans once the spec is approved._
```

### `notes.md`

```markdown
---
slug: <slug>
linear: <issue-id-or-empty>
size: <detected-size>
status: spec
last-updated: <ISO timestamp>
---

## Open questions

## Log

- <ISO timestamp> — created via /start-task
```

### `review.md`

```markdown
_Populated by /pre-merge. Do not edit by hand._
```

## 5. Confirm and suggest

Output to the user:

```
✓ Created .local/active/<slug>/
  size: <detected-size>
  status: spec

Next: describe what you want to do.
  - "Let's design this" / "brainstorm" → invokes superpowers:brainstorming → fills spec.md
  - "Just code it" → skip brainstorming (typical for quick tasks)
  - "What's already known about this area?" → reads .local/system-map/
```

**Do NOT auto-invoke brainstorming or any other skill.** The user describes intent; Claude picks the next step.

## Common mistakes

- Silently picking `big` or `quick` without showing the user the signals.
- Forgetting to check `.gitignore` for `.local/` and `.worktrees/`.
- Auto-chaining into brainstorming — `/start-task` only creates the folder.
- Writing the folder one level up (`../<repo>_*`) — that's the old convention. Use `git rev-parse --show-toplevel`.
- Forgetting to set the `status: spec` and `last-updated` fields in `notes.md` front-matter.
- Creating multiple folders for what should be one task — confirm the slug before creating.

## Edge cases

- **Multiple active tasks already present:** that's fine — `notes.md`'s `last-updated` field disambiguates the "current" task. Show `/status`-like summary so the user sees what's already in flight.
- **Linear MCP returns no active issue:** fall back to argument or prompt. Do not block.
- **Slug already exists:** ask whether to resume the existing task (and `touch .local/active/<slug>/notes.md` to make it current) or pick a different slug.
- **Repo has no `.gitignore`:** create one with the two entries.
