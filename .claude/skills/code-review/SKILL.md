---
name: code-review
description: Review a pull request or Graphite stack. Use when asked to review a PR, check someone's code, give feedback on changes, or assess a diff for issues.
---

# Code Review

Review a PR and provide structured feedback.

## 1. Identify the PR

- Accept a PR number, GitHub/Graphite URL, or branch name from the user.
- If none provided, ask which PR to review.
- Run `gh pr view <number> --json title,body,baseRefName,headRefName,files` to understand scope.

## 2. Read the changes

- Get the full diff: `gh pr diff <number>`.
- For large PRs, read the diff file-by-file using `gh pr diff <number> -- <path>` or read individual changed files.
- If it's a Graphite stack, review each PR in the stack separately (bottom-up) using `gh pr list --search "head:<branch>"` or Graphite links.
- Read surrounding context of changed files when the diff alone isn't enough to understand impact.

## 3. Analyze

Check for:

- **Correctness**: Logic errors, edge cases, off-by-one errors, race conditions.
- **Security**: Injection vulnerabilities, auth bypasses, credential exposure, OWASP top 10.
- **Types**: Incorrect types, unsafe casts, missing null checks.
- **Architecture**: Does it follow existing patterns? Is the abstraction level appropriate?
- **Testing**: Are the changes tested? Are important cases missing?
- **Naming**: Are variables, functions, and files named clearly?
- **Project conventions**: Check against CLAUDE.md rules (e.g. no duck typing, prefer strict object shapes, use `assertUnreachable`, wrap `JSON.parse` in try/catch).

Do NOT flag:

- Nitpicks on style that linters already catch.
- Missing docs/comments unless the logic is genuinely unclear.
- Hypothetical future issues that don't apply to the current change.

## 4. Present findings

- Organize feedback by severity:
  - **Blocking**: Must fix before merge (bugs, security, broken behavior).
  - **Suggestions**: Worth considering but not blocking (better patterns, simplifications).
  - **Praise**: Call out things done well.
- For each item, reference the file and line, explain the issue, and suggest a fix when possible.
- If the PR looks good, say so clearly.

## 5. Submit review (optional)

- Ask the user if they want to submit the review as a GitHub comment.
- If yes, use `gh pr review <number>` with `--approve`, `--comment`, or `--request-changes` as appropriate.
- Format the review body clearly with the findings from step 4.
