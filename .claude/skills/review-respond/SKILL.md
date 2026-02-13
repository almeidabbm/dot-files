---
name: review-respond
description: Address PR review feedback on a Graphite stack
user_invocable: true
---

# Respond to PR Review Feedback

Address review comments on one or more branches in a Graphite stack.

## 1. Understand the feedback

- Ask the user which PR/branch has review feedback, or accept a Graphite/GitHub PR link.
- Read the review comments using `gh pr view <number> --comments` or the GT MCP tools.
- Summarize the feedback and confirm the plan with the user before making changes.

## 2. Apply fixes

- Checkout the target branch: `gt checkout <branch-name>`.
- Make the requested changes.
- Run related tests to ensure the fix doesn't break anything.
- Amend the branch using `gt modify` (not raw git amend).
- Run `gt restack` to rebase all branches above the modified one.
- If `gt restack` hits merge conflicts, **stop and show the conflicts to the user** before doing anything.

## 3. Verify the stack

- Run `gt log` to confirm the stack is clean after restacking.
- Run related tests on the branches above to make sure they still work after the rebase.

## 4. Wrap up

- Ask the user: **"Should I submit the updated stack (`gt submit --stack`), or will you handle it?"**
  - If submit: run `gt submit --stack`.
  - If the user will handle it: wait for confirmation before finishing.
