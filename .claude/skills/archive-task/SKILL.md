---
name: archive-task
description: Use after a PR has been merged to close out the task — moves .local/active/<slug>/ to .local/archive/<slug>/, optionally graduates spec or review highlights into the repo's docs/ folder, and prompts for system-map updates. Triggered by "archive this task", "we're done with X", or detected automatically when a PR is merged.
---

# Archive Task

## Overview

The clean lifecycle transition from `active/` → `archive/`. This is also where private working memory has the chance to **graduate into trusted repo documentation** (`docs/`) and where durable architectural intelligence accumulates in `system-map/`.

This is a deliberately interactive skill — the graduation decisions are too consequential to automate.

## When to use

- A PR has just been merged (or is about to be).
- The user says "archive this", "we're done with X", "wrap this up".
- `gh pr view --json state` shows the current branch's PR as `MERGED`.

## Process

### 1. Identify the task

Default: the current task (most recently modified `.local/active/<slug>/`).

If multiple candidates or ambiguity, ask:

```
Multiple active tasks. Which to archive?
  1. 2026-05-24-fix-dashboard-filter-persistence  [status: ready-to-ship]
  2. 2026-05-20-plan-multi-tenant-support         [status: plan]
```

### 2. Verify completion

Check task is genuinely done before archiving:

- `notes.md` `status` should be one of: `ready-to-ship`, `merged`. If `implementing` or earlier, ask the user to confirm — archiving an incomplete task is unusual but allowed.
- Optionally: `gh pr view --json state,mergedAt` on the task's branch to confirm `MERGED`. If the PR isn't merged, ask: "PR isn't merged yet — archive anyway?"

### 3. Scan for doc destinations

```
find . -type d \( -name 'docs' -o -name 'adr' -o -name 'runbooks' -o -name 'architecture' \) -not -path './node_modules/*' -not -path './.local/*' -not -path './.worktrees/*'
```

Report what's found:

```
Doc destinations available in this repo:
  • docs/
  • docs/architecture/
  • docs/runbooks/
  (No docs/adr/ found.)
```

If the repo has no `docs/` at all, skip graduation prompts — just archive.

### 4. Offer graduation, per artifact

#### `spec.md` → repo docs

Almost always relevant for **planning tasks** (slug starts with `plan-`) and **complex features**. Rarely relevant for bugfixes.

```
Graduate spec.md → docs/architecture/<feature>.md?
  Suggested filename: multi-tenant-support.md
  [Y/n/different-path]
```

If yes:
- Copy `spec.md` content.
- Strip working-memory headers (status, dates) — keep substantive sections.
- Add a header: `# <Title>` + `_Originally drafted YYYY-MM-DD as part of task <slug>._`
- Write to the chosen path.
- Stage as a git commit on a fresh branch (per CLAUDE.md: never commit to main).

#### `review.md` highlights → runbooks

Relevant when `/pre-merge` produced operational insights worth retaining (e.g., new monitoring approach, new failure mode discovered).

```
Graduate review.md highlights → docs/runbooks/<feature>.md?
  [Y/n/different-path]
```

If yes:
- Extract only the "CONFIRMED-FINE" hardening checklist items + any system-level findings worth keeping.
- Skip the BLOCKING/SUGGESTION lists (those were specific to this PR).
- Write a clean runbook-style doc.
- Stage as a commit.

#### `plan.md` and `notes.md`

Typically do not graduate. They are working memory.

### 5. Prompt for `system-map/` updates

This is the loop that grows the highest-leverage long-term asset. Be specific:

```
Did this work uncover anything durable?
  • A new invariant (something that must hold)?
  • A dangerous area (touch carefully in the future)?
  • A concrete pitfall (gotcha we hit)?
  • A module/area deep-dive (how something actually works)?

If yes, I'll help craft an entry in .local/system-map/. (You can also say "no, nothing new".)
```

If yes, for each entry:
1. Determine prefix: `inv-` / `area-` / `danger-` / `pitfall-`.
2. Generate a slug-style filename.
3. Use the standard template (see "system-map template" below).
4. Write to `.local/system-map/<prefix>-<slug>.md`.
5. Update `.local/system-map/INDEX.md` with a new line.

#### system-map template

```markdown
# <one-line title>

**Type:** invariant | area | danger | pitfall
**First captured:** YYYY-MM-DD (from task <slug>)
**Last updated:** YYYY-MM-DD

## What
<1-2 sentences>

## Why this matters
<what breaks if you don't know this>

## How to recognize when it applies
<concrete signals — file paths, error patterns, code shapes>

## What to do
<actions, cautions, or links>

## Related
- [[<other-entry>]] / past incidents / task slugs
```

### 6. Move the folder

```
mv .local/active/<slug>/ .local/archive/<slug>/
```

Update `notes.md`'s `status: archived` and `last-updated`.

### 7. Output summary

```
✓ Archived: 2026-05-24-fix-dashboard-filter-persistence
  • Spec graduated → docs/architecture/dashboard-state.md (staged on branch docs/dashboard-state)
  • System-map: 1 new entry — area-dashboard-state.md
  • Moved active/ → archive/
```

### 8. (Future) Post to Linear

If Linear MCP is available and the task has a `linear:` ID, post a summary comment with:
- Link to the archived spec (or to the graduated `docs/` doc if it exists).
- List of system-map entries created.
- Pre-merge confirmed-fine summary.

Out of scope for v1; the skill should NOT block on it.

## Common mistakes

- Graduating a half-baked spec into `docs/` — review before staging. If unclear, ask the user.
- Graduating `plan.md` or `notes.md` — they are working memory; almost never graduate.
- Skipping the system-map prompt — this is where long-term value compounds. Always ask, even if briefly.
- Committing graduated docs directly to main — per CLAUDE.md, create a branch first.
- Moving the folder before the user confirms graduation choices — the user might want to revise something.
- Forgetting to update `INDEX.md` when adding to `system-map/`.

## Edge cases

- **PR not merged yet:** ask explicitly. Sometimes the user wants to archive prematurely (abandoned work).
- **Slug already exists in `archive/`:** append a suffix (e.g. `-take-2`) and warn the user.
- **No `docs/` folder in the repo:** skip graduation prompts entirely; just move the folder and prompt for system-map updates.
- **Graduation file already exists at the target path:** ask whether to overwrite, merge, or use a different filename.
- **User says "no graduation, no system-map, just archive":** respect it. Move the folder, exit.
