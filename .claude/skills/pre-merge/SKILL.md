---
name: pre-merge
description: Use before merging your own work to verify production safety. Runs an adversarial review (production failure modes) plus a hardening checklist (observability, rollback, migrations) against spec, plan, system-map, and the actual diff. Produces a go/no-go report. Use when the user says "ready to ship", "can we merge?", "is this safe?", or after tests pass.
---

# Pre-Merge

## Overview

The rigorous pre-merge confidence gate. Runs **adversarial review** (production failure-mode lens) followed by a **hardening checklist** (operational readiness), informed by the spec, plan, system-map, and the actual diff.

This is the central confidence ritual of the workflow. It complements `/code-review` (which checks the diff itself for correctness/security) and does NOT duplicate it. See "Composition" below.

## When to use

- After implementation is complete and tests pass.
- Before requesting human review or pushing to remote.
- When the user asks "ready to ship?" / "can we merge?" / "is this safe?"

**Modes:**
- Default: against the diff (post-implementation).
- `--on-plan`: Phase 1 only, against `spec.md` + `plan.md`, before any code is written. Useful for `big` tasks to catch design-level risks early.

## Inputs

1. **Current task:** the most recently modified folder under `.local/active/`. If ambiguous, ask.
2. **`spec.md`** — what was supposed to be built. Read in full.
3. **`plan.md`** — how it was decomposed.
4. **The diff:**
    ```
    git diff $(git merge-base HEAD <trunk>)...HEAD
    ```
    Trunk = `main` (or whatever `git symbolic-ref refs/remotes/origin/HEAD` resolves to).
5. **`.local/system-map/*.md`** — all entries. Match `inv-`, `danger-`, `pitfall-` files whose "How to recognize when it applies" patterns appear in the diff.
6. **`notes.md` front-matter** — `size` field drives rigor (see below).

## Process

### Phase 1 — Adversarial Review (production failure-mode lens)

For each category, scan the diff and write findings to `review.md`. Tag each finding `BLOCKING` / `SUGGESTION` / `CONFIRMED-FINE`.

- **Concurrency & race conditions** — shared state, parallel writes, ordering assumptions.
- **Retry / idempotency / partial-failure safety** — what happens on retry? what if step 2 fails after step 1 succeeded?
- **Migration ordering & backward compatibility** — schema changes before or after code? rollback path?
- **Auth / authorization edge cases** — new endpoints checked? new resources permission-gated?
- **Hidden coupling** — does this break an invariant another part of the system relies on?
- **Performance** — N+1, missing indexes, hot-path allocations, query plan changes.
- **Observability gaps** — what would break silently? logs/metrics for new behavior?
- **Spec gaps** — does the diff implement what `spec.md` says? scope creep? missed requirements?
- **`system-map` matches** — for each matching entry, cite the file and the specific concern. These are HIGH-WEIGHT findings.

### Phase 2 — Hardening Checklist (operational readiness)

Each item: `PASS` / `FAIL` / `N/A` with reasoning. Findings from Phase 1 inform answers.

- **Observability:** logs + metrics for new behavior?
- **Rollback:** revertible without data loss?
- **Migration:** backward-compatible? ordered correctly?
- **Compatibility:** public contracts preserved?
- **Performance:** bounded? measured?
- **Ops:** runbook entry or operational note needed?

### Size-aware rigor

Adjust depth based on `notes.md` `size`:

- **`quick`:** 5 lightweight checks — regression, rollback, observability, spec match, system-map match. Skip the rest unless something specific triggers.
- **`standard`:** full Phase 1 + Phase 2 as above.
- **`big`:** full Phase 1 + Phase 2 + cross-cutting checks — multi-PR consistency (read sibling branches in the stack), migration ordering across PRs, mandatory system-map update prompts.

## Output

### `review.md`

Overwrite the file (it's a working document; don't accumulate stale findings). Structure:

```markdown
# Pre-Merge Review — <slug>

**Date:** YYYY-MM-DD HH:MM
**Size:** <size>
**Diff:** <N> files, +<adds>/−<dels>

## Summary

- 🔴 BLOCKING: <n>
- 🟡 SUGGESTIONS: <n>
- 🟢 CONFIRMED-FINE: <n>

## Phase 1 — Adversarial Review

### Concurrency
- 🔴 BLOCKING — `path/to/file.ts:120` — <description>
- 🟢 CONFIRMED-FINE — no shared mutable state introduced

### Retry / Idempotency
…

### Migrations
…

(only include categories with findings or that are explicitly checked)

### System-Map Matches

- 🔴 `.local/system-map/danger-migration-ordering.md` — this diff touches migrations; the entry warns about <X>. <Specific issue or "checked, OK">.

## Phase 2 — Hardening Checklist

- ✅ Observability — added counter `dashboard.filter.persist.errors`
- ❌ Rollback — schema change in PR is non-reversible; needs split migration
- ✅ Compatibility — public API unchanged
- ✅ Performance — added index covers new query
- ⚠ Ops — runbook update suggested but not required

## Verdict

- **BLOCKING items must be resolved before merge.**
- Suggestions are optional but worth considering.
```

### Console summary

Print a compact summary with the BLOCKING items inlined so the user sees what to fix without opening the file:

```
/pre-merge: 1 BLOCKING, 2 SUGGESTIONS, 11 CONFIRMED-FINE

BLOCKING:
  • path/to/file.ts:120 — race condition: two concurrent writes to filter state can lose one update

Full report: .local/active/<slug>/review.md
```

### Update `notes.md` front-matter

- If 0 BLOCKING: set `status: ready-to-ship`.
- If ≥1 BLOCKING: set `status: review`.
- Always update `last-updated`.

## Composition with `/code-review`

Different lenses, both valuable on your own PRs:

- **`/code-review`** → diff-level correctness, security, types, architecture. Catches the bug *in the code*.
- **`/pre-merge`** → production-failure-modes vs. spec + plan + system-map. Catches the bug *in the system behavior*.

Run both before submit. If `review.md` already exists from a recent `/pre-merge`, `/code-review` should reference it rather than restate its findings.

## Common mistakes

- Treating `/pre-merge` as a code-review skill — it is NOT. It is wider and uses the spec, plan, and system-map as context.
- Not reading `system-map/` — those entries are durable knowledge and the highest-signal findings.
- Skipping size-aware rigor — a `quick` task gets light coverage; a `big` task gets the full battery.
- Accumulating stale findings — overwrite `review.md` on each run.
- Updating `status` to `ready-to-ship` while BLOCKING items exist — verify count first.
- Running against the wrong base — use the merge-base with trunk, not `HEAD~1`.

## Edge cases

- **No `.local/active/<slug>/` exists:** the user hasn't run `/start-task`. Offer to run it now, or fall back to a quick gate without spec/plan (degraded mode — say so).
- **`spec.md` empty:** missing context. Warn the user; gate becomes more limited.
- **No diff (clean tree):** print "Nothing to review — your working tree is clean."
- **`--on-plan` mode but no `spec.md` content:** abort with a message.
- **Cross-stack review (Graphite):** if the current branch is mid-stack, review the cumulative diff against the stack's base, not just the parent branch.
