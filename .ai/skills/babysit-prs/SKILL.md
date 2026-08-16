---
name: babysit-prs
description: Use when running one PR-health pass — polling CI on open pull requests, deciding whether a failure is a flake, a regression, or a broken trunk, rerunning what is worth rerunning, and reporting the change to Slack.
---

# Babysit a PR's health

One pass over every pull request in the watch set. A pass is bounded: it reads
state, acts on what moved, writes state, reports, and exits. The loop lives in
`babysit.sh`, not in your head — never sleep and poll inside a pass.

Every failure resolves to exactly one **verdict**, and the verdict decides both
the action and the message:

| Verdict | Means | Action |
| --- | --- | --- |
| `flake` | The failure is not about this code | Rerun once, report the flake |
| `regression` | This PR introduced it | Report with the evidence, rerun nothing |
| `trunk-broken` | Trunk is failing the same way | Report once, rerun nothing |
| `unknown` | The evidence is thin | Report as unknown, rerun nothing |

## Guardrails

These hold for the whole pass, whatever the verdict:

- The only write action available is `gh run rerun`. Merging, pushing,
  approving, closing, commenting, and pushing review state are outside this
  agent's remit — the human owns them.
- One rerun per workflow per head SHA. The state file is what remembers, so read
  it before rerunning, and write it after.
- At most 6 reruns across a whole pass. Report the ones you skipped over that
  cap rather than dropping them silently.

## 1. Collect the watch set

```sh
gh search prs --author=@me --state=open --json number,repository,title,url,isDraft
gh search prs --review-requested=@me --state=open --json number,repository,title,url,isDraft
```

Union the two, keyed by `repo#number`. Drafts stay in the set — a draft's CI is
still worth babysitting — but they are labelled as drafts in the report.

Done when every open PR in both queries has a head SHA resolved
(`gh pr view <n> --repo <r> --json headRefOid,headRefName,baseRefName`).

## 2. Skip what has not moved

Read `~/work/state/babysit.json` (shape in `state.md`). For each PR, compare the
head SHA and each check's conclusion against what the state records.

Skip the PR entirely when the head SHA is unchanged **and** every check holds the
conclusion the state already reports. Most passes skip most PRs; that is the
design, and it is what keeps a pass cheap enough to run every ten minutes.

Done when the pass holds a list of PRs whose checks changed since the last pass.

## 3. Classify each failure

For each failing check, pull the evidence before deciding:

```sh
gh run view <run-id> --repo <repo> --log-failed   # the failing step's output
gh pr diff <n> --repo <repo> --name-only          # what this PR touches
gh run list --repo <repo> --branch <base> --workflow <wf> --limit 5 --json conclusion
```

Walk the signals in order and stop at the first that fires — they are ranked by
how much they actually prove:

| Signal | Verdict |
| --- | --- |
| The same workflow is failing on the last few trunk runs | `trunk-broken` |
| A rerun of this exact SHA already passed (state records it) | `flake` |
| The log matches an infra pattern — runner lost, OOM, `ECONNRESET`, `ETIMEDOUT`, registry 5xx, rate limit, cancelled | `flake` |
| The failing test's file appears in this PR's diff | `regression` |
| A source file the failing test exercises appears in the diff | `regression` |
| This workflow passed on the PR's previous head and this push touches files the failure names | `regression` |
| None of the above | `unknown` |

A `regression` verdict carries its evidence into the report: the failing test
name, the assertion line from the log, and the diff path that implicates it. A
verdict a human cannot check is worth less than no verdict.

Done when every failing check on every moved PR carries a verdict and, for
`regression`, its three pieces of evidence.

## 4. Rerun the flakes

Rerun only `flake` verdicts, and only when the state shows no rerun yet for this
workflow at this SHA:

```sh
gh run rerun <run-id> --repo <repo> --failed
```

Record the rerun in the state file before reporting, so a pass that dies
half-way cannot double-spend the budget.

A rerun that fails again the same way is no longer a flake — reclassify it as
`unknown` on the next pass and say that the retry did not clear it.

Done when every rerun is either issued and recorded, or skipped with a recorded
reason.

## 5. Report the transitions

Report a **transition** — a verdict that differs from what the state last
reported for that `(pr, workflow, sha)`. A failure already reported stays quiet
until it changes. This is what makes the loop liveable at a ten-minute cadence.

Append one section per pass to `~/work/reports.md`, newest at the bottom, covering
every PR that moved. Nobody is watching this file live, so it is a log a human
reads later — date every section and keep each finding self-contained rather than
referring back to an earlier pass.

Order the entries by what most needs a human: `regression` first, then `unknown`,
then `trunk-broken`, then `flake`, then recoveries.

```markdown
## 2026-08-15T14:10Z — 3 moved

### 🔴 regression — lightdash/lightdash#1234 Fix chart tooltips
`CI / unit` — `ChartTooltip.test.tsx` fails at `expect(tooltip).toBeVisible()`
diff touches `packages/frontend/src/components/ChartTooltip.tsx`
https://github.com/lightdash/lightdash/pull/1234/checks

### ♻️ flake — lightdash/lightdash#1240 Bump deps
`CI / e2e` — runner lost connection; rerun issued (1/1)

### ✅ recovered — lightdash/lightdash#1238
All checks green.
```

A pass where nothing moved writes nothing. An empty `reports.md` means healthy,
and `~/work/babysit.log` is where a human confirms the pass actually ran.

Done when `~/work/reports.md` holds this pass's section and the state file
records the verdicts it reported.
