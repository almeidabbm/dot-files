---
name: code-review
description: Use when asked to review a diff, branch, pull request, or stack for correctness, security, architecture, typing, tests, and naming. This is the code-quality lens, not the production-safety lens.
---

# Code Review

Review the change itself for quality and correctness.

This skill complements `pre-merge`:

- `code-review` checks the diff for correctness, security, types, architecture, testing, and naming.
- `pre-merge` checks whether the system behavior is safe to ship.

## 1. Identify the review target

Accept any of:

- a PR number
- a PR URL
- a branch name
- the current uncommitted diff

If GitHub CLI is available and the user gave a PR, use `gh pr view` and `gh pr diff`.
Otherwise use local `git diff` and surrounding file context.

## 2. Read the changes

- Read the diff file by file when needed.
- Read surrounding context when the diff alone is not enough.
- If this is a stack, review it bottom-up rather than as one giant combined diff.

## 3. Analyze

Look for:

- correctness bugs
- security issues
- type safety problems
- architectural mismatches
- missing or weak tests
- confusing naming
- divergence from established project conventions

Do not focus on formatting or style that linters already enforce.

## 4. Present findings

Order findings by severity:

- Blocking
- Suggestions
- Praise

For each issue, include file and line references when possible and explain the impact clearly.

If the change looks good, say that explicitly.

## Optional follow-up

If the user wants the review submitted to GitHub and `gh` is available, prepare a review body and submit it with the appropriate mode.
