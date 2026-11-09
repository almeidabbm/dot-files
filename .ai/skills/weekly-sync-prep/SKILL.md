---
name: weekly-sync-prep
description: Prepare a short pack for my weekly sync from the private project state files, then save it without sending anything. Load when asked to prep the weekly sync, or when a scheduled run asks for it.
---

# Weekly sync prep

## Inputs

- `weekly-sync.md` in the private plans folder (`project-state` skill): which repositories, trackers, and projects to cover, and any extra sections. If it is missing, ask.
- Every `<project>/STATE.md` in that folder.
- `ideas.md` in that folder.

## Steps

1. Refresh each active project's `STATE.md` against the repository and tracker, following the `project-state` rules.
2. Write `weekly-sync/<YYYY-MM-DD>.md` in the plans folder:
   - **Projects:** one line each — where it stands and its release step.
   - **To discuss:** decisions where another view would help, each with my recommendation.
   - **Coming up:** work likely to land in the next few weeks, from the tracker and recent threads.
   - **Pitch:** only when an idea in `ideas.md` has enough evidence, a one-page pitch: problem, evidence, rough shape, cost, what it would replace. Skip the section otherwise; never pad it.
3. Keep the pack readable in two minutes. Delete packs older than four weeks.

Never send, post, or share the pack. Report its path.
