---
name: pre-merge
description: Use before merging your own work to verify production safety. Reviews spec, plan, system-map knowledge, and the actual diff to produce a go or no-go report with blocking issues, suggestions, and a hardening checklist.
---

# Pre-Merge

Run a production-safety review of the current task. This is broader than ordinary code review and focuses on failure modes, rollout safety, and operational readiness.

## Inputs

1. The current task: the most recently modified folder under `.local/active/`
2. `spec.md`
3. `plan.md`
4. `notes.md` frontmatter
5. matching `.local/system-map/*.md` entries
6. the current diff against trunk

Use the merge base with trunk rather than `HEAD~1`.

## Process

### Phase 1: adversarial review

Check for:

- concurrency and race conditions
- retry, idempotency, and partial-failure safety
- migration ordering and backward compatibility
- auth and authorization edge cases
- hidden coupling and invariant breaks
- performance regressions
- observability gaps
- spec mismatch or scope creep
- any relevant `system-map` warnings

Tag findings as `BLOCKING`, `SUGGESTION`, or `CONFIRMED-FINE`.

### Phase 2: hardening checklist

Mark each item `PASS`, `FAIL`, or `N/A`:

- observability
- rollback
- migration safety
- compatibility
- performance
- ops or runbook needs

## Size-aware rigor

- `quick`: lightweight pass over regression risk, rollback, observability, spec match, and `system-map`
- `standard`: full phase 1 and phase 2
- `big`: full phase 1 and phase 2 plus cross-PR consistency, migration ordering across the stack, and prompts for `system-map` updates

## Output

Overwrite `.local/active/<slug>/review.md` with a fresh report.

Structure:

```markdown
# Pre-Merge Review - <slug>

**Date:** YYYY-MM-DD HH:MM
**Size:** <size>
**Diff:** <N> files, +<adds>/-<dels>

## Summary

- BLOCKING: <n>
- SUGGESTIONS: <n>
- CONFIRMED-FINE: <n>

## Phase 1 - Adversarial Review

## Phase 2 - Hardening Checklist

## Verdict
```

Also print a compact console summary that includes the blocking items inline.

Update `notes.md`:

- `status: ready-to-ship` if there are zero blocking items
- `status: review` if there is at least one blocking item
- always refresh `last-updated`

## Edge cases

- If there is no active task, offer degraded mode and say what context is missing.
- If `spec.md` is empty, warn that the review has reduced coverage.
- If the working tree is clean and there is no diff, say there is nothing to review.
