---
name: status
description: Use when the user asks what they were working on, wants to see active tasks, or seems disoriented about in-flight work. Reads central agent memory and produces a compact global status view with next-step guidance.
---

# Status

Produce a read-only summary of active tasks from central agent memory.

## Process

1. Resolve the current repository when inside one.
2. Run `agent-memory list --state active` and read each returned `notes.md` and
   `task.json`.
3. Parse `id`, `slug`, `ticket`, `repositories`, `size`, `status`, and
   `last-updated`.
4. Resolve the current task with `agent-memory current --repo <checkout>` when
   possible. Never use file modification time.
5. Build one next-step suggestion per task.

Suggested next steps:

- `spec` -> design or complete `spec.md`
- `plan` -> turn `plan.md` into approved implementation steps
- `implementing` -> continue coding, then run related tests and `pre-merge`
- `review` -> fix blocking items from `review.md`, then rerun `pre-merge`
- `ready-to-ship` -> submit the PR (`gh stack submit --open` inside a stack)
- `merged` -> archive the task

If status is `review`, include the number of blocking items from `review.md`.

## Output

Keep the output to one screen when possible:

```text
▸ <slug> [<status>, <size>]
  <repository-summary> · <ticket-or-empty> · next: <suggestion>
```

Order the explicitly resolved current task first, then `last-updated`
descending. Do not expose private ticket URLs or machine paths outside the
user's local response.

## Edge cases

- If there are no active tasks, suggest `start-task`.
- If `agent-memory current` is ambiguous, show the candidates and recommend an
  explicit `agent-memory bind`.
- Flag malformed manifests/frontmatter and continue.
- Do not modify files.
