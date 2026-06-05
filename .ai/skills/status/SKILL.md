---
name: status
description: Use when the user asks what they were working on, wants to see active tasks, or seems disoriented about in-flight work. Reads .local/active/ and produces a compact status view with next-step guidance.
---

# Status

Produce a read-only summary of active tasks from `.local/active/`.

## Process

1. Resolve the repo root with `git rev-parse --show-toplevel`.
2. Read every `.local/active/*/notes.md`.
3. Parse frontmatter fields: `slug`, `linear`, `size`, `status`, and `last-updated`.
4. Use file mtime to decide which task is current.
5. Build one next-step suggestion per task based on status.

Suggested next steps by status:

- `spec` -> design or fill `spec.md`
- `plan` -> turn `plan.md` into concrete implementation steps
- `implementing` -> continue coding, then run related tests and `pre-merge`
- `review` -> fix blocking items from `review.md`, then rerun `pre-merge`
- `ready-to-ship` -> submit the PR or push with permission
- `merged` -> archive the task

If status is `review`, scan `review.md` and include the number of blocking items inline.

## Output

Keep the output to one screen when possible.

Format each task like:

```text
▸ <slug> [<status>, <size>]
  <linear-or-empty> - next: <suggestion>
```

Order tasks by:

1. current task first
2. then `last-updated` descending

## Edge cases

- If `.local/active/` is empty, say there are no active tasks and suggest `start-task`.
- If frontmatter is malformed, flag it inline and continue.
- If a task folder has no `notes.md`, surface that without crashing.
- Do not modify any files.
