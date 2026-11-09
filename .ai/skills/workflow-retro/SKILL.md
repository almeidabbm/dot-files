---
name: workflow-retro
description: Weekly check of how my agent workflow is going, against agreed targets, plus a monthly scan for AI-workflow practices worth adopting. Proposes changes; never applies them. Load when asked for a workflow retro or review, how the workflow changes are doing, or when a scheduled run asks for it.
---

# Workflow retro

Private paths, all git-ignored:

- `WORK=~/Develop/dot-files/.local/workflow/` holds `metrics.json`, `weekly.json`, `proposals.md`, and `config.md`.
- `config.md` names the scorecard artifact's URL and the plans folder (`project-state` skill) to count weekly sync packs from. If it is missing, ask.

## Weekly

1. Run `python3 -I metrics.py --weeks 12 --plans <plans folder> > $WORK/metrics.json` from this skill's folder, and write the rows to `$WORK/weekly.json` (fields the scorecard reads: every key in the latest row).
2. Upload `weekly.json` to the scorecard as an asset, point its `weekly` dataset at the new `/_blob/` URL with `updated` set to now, and delete the previous asset.
3. Compare the latest full week with the targets on the scorecard. For each metric off target two weeks running, find the cause in that week's sessions (read the user's messages that matched), then name the smallest fix: a rule to reword, a skill step agents skip, or something to delete.
4. Repeated corrections: when the user corrected the same thing three or more times across the week's sessions and it is not yet in `delegate/review-standards.md` or the shared instructions, propose adding it.
5. Rules that keep failing: a rule broken again after it was written is a wording or placement problem. Propose moving it, shortening it, or deleting it, not restating it louder.
6. Append to `$WORK/proposals.md` under the date: at most three proposals, each with the evidence (counts, quoted messages), the exact edit, and what it removes or replaces.

## Monthly (first run of the month)

Scan for practices people actually use when working with coding agents: sources like practitioner write-ups, talks, and maintained skill repositories with sustained use (months, not launch week). Keep a candidate only if all hold:

- It solves friction the metrics or proposals already show.
- It is small: a rule, a skill step, or one skill. Frameworks that install dozens of skills, agents, or hooks are out; the user found a large plugin pack mostly bloat.
- It fits the shared instructions (provider-neutral, owner-reviewed, smallest complete change) or says which instruction it would replace.
- Someone reports using it for real work, with results.

Add at most three to `proposals.md`, each with sources, the friction it targets, and what it replaces or deletes. Proposing nothing is a valid outcome.

## Never

Install, edit skills or instructions, or change targets on your own. The user reviews `proposals.md` and decides. Keep customer names and private paths out of anything public.
