---
name: archive-task
description: Use after a task is merged or otherwise complete to move .local/active/<slug>/ to .local/archive/<slug>/, optionally graduate durable docs into the repo, and capture long-term system-map knowledge.
---

# Archive Task

Archive a completed task and preserve any knowledge worth keeping.

## Process

### 1. Identify the task

Default to the most recently modified folder under `.local/active/`.
If more than one task looks plausible, ask which one to archive.

### 2. Verify completion

Check `notes.md` status. Expected values are `ready-to-ship` or `merged`, but the user may still choose to archive something earlier.

If GitHub CLI is available, optionally confirm whether the task branch PR is merged.

### 3. Scan for doc destinations

Look for repo docs locations such as:

- `docs/`
- `docs/architecture/`
- `docs/runbooks/`
- `adr/`
- `runbooks/`

If none exist, skip graduation prompts.

### 4. Offer graduation

Possible graduation targets:

- `spec.md` -> architecture or design docs
- selected `review.md` operational takeaways -> runbooks

Usually do not graduate `plan.md` or `notes.md`.

When graduating:

- strip working-memory boilerplate
- keep the substantive content
- add a short note tying the doc back to the task slug and original date

### 5. Prompt for system-map updates

Ask whether the task uncovered durable knowledge such as:

- a new invariant
- a dangerous area
- a repeatable pitfall
- a useful area deep-dive

If yes, write entries under `.local/system-map/` using prefixes:

- `inv-`
- `area-`
- `danger-`
- `pitfall-`

Also update `.local/system-map/INDEX.md` when adding entries.

### 6. Move the folder

Move:

- `.local/active/<slug>/` -> `.local/archive/<slug>/`

Then update `notes.md`:

- `status: archived`
- refreshed `last-updated`

## Output

Summarize:

- which task was archived
- whether any docs were graduated
- whether any `system-map` entries were added

## Edge cases

- If the archive destination already exists, append a suffix such as `-take-2`.
- If the user says to skip graduation and system-map updates, respect that and just archive.
