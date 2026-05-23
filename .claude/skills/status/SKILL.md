---
name: status
description: Use when the user asks "where was I?", "what was I working on?", "show me my tasks", or seems disoriented about in-flight work. Reads .local/active/ and produces a one-screen view of all active tasks with their status, size, and suggested next step.
---

# Status

## Overview

A read-only "where am I?" reporter. Single command to regain situational awareness across all in-flight tasks. The single biggest lever against cognitive load when juggling multiple tasks.

## Process

### 1. Resolve repo root

```
$(git rev-parse --show-toplevel)
```

If not in a git repo, exit with a clear message.

### 2. Enumerate active tasks

Read every `.local/active/*/notes.md`. For each:

- Parse YAML front-matter (`slug`, `linear`, `size`, `status`, `last-updated`).
- Note the file's mtime — this determines which task is "current" (most recently modified).

If `.local/active/` is empty:

```
No active tasks. Run /start-task to begin one.
```

### 3. Build the per-task next-step suggestion

Based on the `status` field:

| status            | suggested next step                                                |
| ----------------- | ------------------------------------------------------------------ |
| `spec`            | Run brainstorming to fill `spec.md`                                |
| `plan`            | Run writing-plans to decompose into stacked PRs                    |
| `implementing`    | Continue coding; run tests + `/pre-merge` when done                |
| `review`          | Fix BLOCKING items in `review.md`, then re-run `/pre-merge`        |
| `ready-to-ship`   | Submit the PR (`gt submit` or `git push` + `gh pr create`)         |
| `merged`          | Run `/archive-task` to move to `archive/`                          |
| `archived`        | (Should not appear in `active/`. Surface as inconsistency.)        |

If `status` is `review`, also scan the task's `review.md` and surface the count of `BLOCKING` items inline.

### 4. Output

Print a single-screen view:

```
Active tasks (3):
  ▸ 2026-05-24-fix-dashboard-filter-persistence   [implementing, standard]
      ENG-1234 — next: run tests, then /pre-merge
  ▸ 2026-05-20-plan-multi-tenant-support           [plan, big]
      ENG-1100 — next: review plan.md, create Linear issues
  ▸ 2026-05-18-extract-shared-button               [review, standard]
      ENG-1212 — 2 BLOCKING in review.md, fix and re-run /pre-merge

Current: 2026-05-24-fix-dashboard-filter-persistence
```

**Ordering:**
- Current task first (most recently modified).
- Then by `last-updated` desc.

**Per-line format:**
```
  ▸ <slug>   [<status>, <size>]
      <linear-or-empty> — next: <suggestion>
```

## Common mistakes

- Listing archived tasks — only enumerate `active/`, never `archive/`.
- Showing raw front-matter instead of a digested summary.
- Picking "current" by some heuristic other than `last-updated` (file mtime). One source of truth.
- Modifying any files — this skill is strictly read-only.
- Producing more than one screen of output — keep it scannable. If there are >10 active tasks, summarize the older ones into a single line.

## Edge cases

- **Front-matter missing or malformed in a task's `notes.md`:** flag it inline (`⚠ malformed front-matter`) but don't crash. Continue listing the others.
- **`active/` folder exists but no `notes.md` in a subfolder:** show the slug with `⚠ no notes.md`.
- **Multiple tasks tied for most-recent mtime:** alphabetical tiebreaker on slug.
- **Not in a git repo:** print `Not in a git repository — nothing to show.` and exit.
