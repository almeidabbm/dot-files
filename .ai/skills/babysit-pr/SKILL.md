---
name: babysit-pr
description: Shepherd an open PR to merge — watch CI, fix failures, answer and resolve review threads, then merge once the gate passes. Load when the user says to merge, land, or babysit a PR, or names an extra merge condition.
---

# Babysit PR

The user's "merge" authorizes merging that one PR once the gate passes. Push and sync follow the `git-workflow` skill.

## Gate

Default: **every** check on the head commit is green (not only required ones), no review thread is unresolved, and no review requests changes. A PR with no checks at all (`gh pr checks` reports none) has nothing to wait for; say so in the report. The user may add conditions (an approval, a deploy check, a command that must pass); the gate is all of them together.

## Start

- Identify the PR (`gh pr view --json number,headRefName,baseRefName,mergeStateStatus,reviewDecision`) and work in its branch checkout.
- Read the merge methods the repo allows (`gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed`); when several are allowed, match recent merges on the base branch.

## Loop

Each round, until the gate passes or a stop condition fires:

1. **Wait** for checks to finish: `gh pr checks <pr> --watch`. In Claude Code run it in the background and act on its notification; elsewhere run it in the foreground. Avoid tight polling.
2. **Failed check**: read the cause (`gh run view <run-id> --log-failed`).
   - Caused by the PR: fix it, run the related checks locally, commit, push.
   - Flaky (passes on rerun, unrelated to the diff): rerun once with `gh run rerun <run-id> --failed`.
   - Also failing on the base branch: stop and report.
3. **Review threads**: list unresolved ones:

   ```bash
   gh api graphql -F owner=<owner> -F repo=<repo> -F pr=<number> -f query='
     query($owner:String!,$repo:String!,$pr:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$pr){
       reviewThreads(first:100){nodes{id isResolved path line comments(first:20){nodes{author{login} body}}}}}}}'
   ```

   Each thread ends fixed or answered: fix what is valid; otherwise reply with the reason (the behavior is intended, the finding is wrong, out of scope). Resolve bot threads after fixing or answering; leave a human reviewer's thread for them to resolve unless they asked you to.
4. **Behind base**: sync per `git-workflow`.

A push restarts CI, so the next round waits again.

## Merge

When the gate passes on the current head commit, merge pinned to it: `gh pr merge <pr> --<method> --match-head-commit <sha>`. Confirm with `gh pr view <pr> --json state,mergeCommit`.

## Stop and ask

- A reviewer requests changes that need a product or design decision.
- Three fix rounds without the gate passing; reconsider the approach rather than a fourth round.
- A rebase conflicts: show the conflicts.
- The merge would need `--admin`, a skipped check, or a bypassed branch protection.

## Report

The merge commit, each fix pushed with the check or thread it addressed, threads answered without a change and why, reruns, and anything left open.
