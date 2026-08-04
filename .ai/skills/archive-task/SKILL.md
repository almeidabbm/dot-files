---
name: archive-task
description: Use after a task is merged or otherwise complete to archive it in central agent memory, optionally graduate durable docs into the repo, and capture long-term system-map knowledge.
---

# Archive Task

Archive a completed task and preserve any knowledge worth keeping.

## Process

### 1. Identify the task

Resolve the task with `agent-memory current --repo <checkout>`. If resolution is
ambiguous, ask which task to bind or archive. Never use modification time.

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

For each affected repository, resolve the destination with
`agent-memory system-map --repo <checkout>`. Write entries using prefixes:

- `inv-`
- `area-`
- `danger-`
- `pitfall-`

Also update `INDEX.md` in each affected repository namespace.

### 6. Archive the task

Run `agent-memory archive <task-id-or-slug>`. It updates the manifest and
`notes.md`, then moves the task atomically into central archive memory.

## Output

Summarize:

- which task was archived
- whether any docs were graduated
- whether any `system-map` entries were added

## Edge cases

- If the archive destination exists, stop and inspect the identity collision;
  do not invent a second folder name.
- If the user says to skip graduation and system-map updates, respect that and just archive.
