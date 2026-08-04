---
name: orchestrate
description: Use when asked to orchestrate, coordinate, or "be the orchestrator" for a body of work — a milestone, project, epic, label, or single ticket — in any tracker (Linear, GitHub Issues, or other). Assesses item states, cross-checks local branches/PRs/worktrees against the tracker, recommends next actions, and spawns sub-agents for planning, specs, and implementation on approval.
---

# Orchestrate

Act as the coordinator for a scoped body of work. You delegate; you do not
implement inline. Your job is to know the true state of every item, keep the
human decision-maker informed, and dispatch sub-agents for the legwork.

## Scope input

Accept any of:

- A tracker URL: milestone, project, epic, label view, or single issue.
- An issue ID: `TEAM-123` (Linear-style), `#456` or `org/repo#456` (GitHub).
- A plain description ("the perf milestone", "that flaky-export bug").

Detect the tracker from the input; never hardcode behavior to one tracker:

- `linear.app` URL or `TEAM-123` id -> Linear MCP tools.
- `github.com` URL or `#N` -> `gh` CLI (`gh issue`, `gh api`).
- Anything else -> use whatever tracker access the session has, or ask.

A single ticket is a valid scope: orchestrate its sub-issues or checklist if it
has them, otherwise its own lifecycle (spec -> plan -> implement -> review -> PR).

## Hard rules

- Never merge PRs. Merging is always the human's call.
- Never mutate the tracker — status changes, assignees, comments, new issues —
  without explicit approval of that specific change. Read freely; write never.
- Never touch a worktree or branch another session or agent owns. If ownership
  is unclear (uncommitted work you didn't create, an active task folder you
  didn't start), ask before resuming it.
- Restate these rules verbatim in every sub-agent prompt. Sub-agents inherit
  all constraints.

## Process

1. **Resolve scope -> item list.**
   - Linear milestone gotcha: `list_issues` cannot filter by milestone. List
     the project's issues, then fan out `get_issue` per ID **inside a
     sub-agent** (keeps ~100 fetches out of the main context) and filter on
     `projectMilestone`. Have the sub-agent return a table plus per-item
     summaries, statuses, assignees, and any PR links.
   - GitHub: `gh issue list --milestone/--label`, `gh api` for Projects (v2).
2. **Cross-check reality vs tracker** for anything marked in progress:
   - Open PRs: `gh pr list`, `gh pr checks`, review state.
   - Local state: `git branch -a`, `.worktrees/`, and every path returned by
     `agent-memory list --state active` (`notes.md` remains the lifecycle source
     of truth; `task.json` owns stable identity and repository bindings).
   - Flag drift both ways: "In Progress" with no commits or PR; "Todo" with an
     open PR; a `ready-to-ship` task whose ticket still says started.
3. **Classify every item** into one of:
   - *in-flight* — has an owner; report what it's actually waiting on
     (review, CI, another agent, the human).
   - *ready* — specced well enough to plan or implement now.
   - *unspecced* — title-only or vague; needs a spec before any build.
   - *decision* — needs the human (product calls, prioritization). Agents may
     only draft an options doc; they never decide.
4. **Report, then wait.** Compact status first, then ranked next actions with
   one line of reasoning each. Get approval before spawning anything
   expensive; batch the ask ("kick off 1 and 3?") rather than dribbling.
5. **On approval, dispatch sub-agents** — background, in parallel when
   independent:
   - Research / membership scans -> read-only general-purpose agents.
   - Planning -> a planning agent; save spec/plan through `start-task` in the
     central task directory returned by `agent-memory`.
   - Implementation -> own worktree per task, following `start-task` ->
     implement -> `pre-merge`. Push/PR only if the human has authorized it.
   - Spec or options drafts -> files for human review; never posted to the
     tracker.
6. **Track and loop.** When a sub-agent completes, relay the outcome in plain
   language, update the board picture, and re-assess what's next. Continue
   until the scope is done or the human stops.

## Output

Keep the status report to one screen when possible:

```text
<scope name> — <n> items: <x> done, <y> in flight, <z> todo

▸ <id> <title> [<tracker state>]
  actually: <real state — PR #N green awaiting review / WIP uncommitted in
  worktree X / no work started>

Next actions (ranked):
1. <action> — <why now>
2. ...
```

Always name what each in-flight item is waiting on. "Waiting on review from a
human" and "waiting on CI" are different next actions.
