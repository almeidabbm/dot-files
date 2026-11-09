---
name: project-state
description: Keep a short private state file per project so any session or tool can resume without asking the user where things stand. Load at the start of work on a tracked project, before compaction or handoff, when a decision is made or a release step changes, and when writing a spec, slices, a risk map, or an idea.
---

# Project state

## Where

The private plans folder is git-ignored and shared by every worktree:

```bash
"$(git rev-parse --path-format=absolute --git-common-dir)/../.local/plans/"
```

Each project gets `<project>/STATE.md`; specs, slice lists, and risk maps sit next to it. If the folder does not exist, ask the user before creating it. Nothing in it goes to a tracker, PR, or public repository.

## STATE.md

```markdown
# <project>
Last checked: <YYYY-MM-DD>
Release type: <experimental behind a flag | full launch | behaviour change | fix>, step <n> of <m> (see ../release-playbook.md)

## Waiting on the user
- <decision, with your recommendation>

## Decided
- <decision>: <why, one line>

## In flight
- <PR or branch link>: <state>, owner <tool and session>

## Environments
- <url>: <what it runs, flag state>

## Could break
- <existing behaviour the work touches>: <how it is verified>
```

## Rules

- Read it before starting work on the project; update it before ending the session.
- Overwrite, never append. Delete finished items; history lives in PRs and the tracker.
- Keep it under about 60 lines. Longer means it is being used as a log.
- If `Last checked` is older than 7 days, verify it against the repository and tracker, rewrite it, then trust it.
- When the release reaches its last step, delete the project folder.
- Customer names may appear here, never in anything that leaves this folder.

## Ideas

`ideas.md` in the plans folder holds only ideas that could shape the product's future: a new product area, a change in how customers work, or something that spans several quarters. Add a two-line entry (the idea, the evidence) when you notice one; never act on it. Smaller ideas go to the normal backlog or nowhere.
