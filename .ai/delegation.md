# Delegation

Use when a bounded assignment benefits from a separate worker. Keep the main conversation focused on the user's goal and decisions; return useful evidence from workers instead of their full exploration logs.

## Decide And Brief

- Keep work local when it is small, depends on continuous shared reasoning, or cannot be separated without extensive coordination. A fixed spec → implementation → review pipeline is unnecessary.
- Delegate independent investigation, a defined implementation, or a focused review. State the assignment, model, and reason briefly in a progress update.
- Give a specification worker the problem and open questions; give an implementation worker the agreed behavior and acceptance criteria. Keep unresolved product decisions visible to the user.

Each brief must include:

1. **Role and goal:** worker, bounded objective, and what is outside scope.
2. **Context:** relevant decisions, file or source references, applicable instruction and skill paths, and necessary facts from the conversation. Do not assume history, tools, or skills are inherited.
3. **Workspace and ownership:** exact repository/worktree directory, allowed edits or read-only assignment, and whether Git actions are assigned.
4. **Done when:** observable acceptance criteria and relevant verification commands where known.
5. **Return:** findings or changes with file/source references, checks actually run and their results, unresolved issues, and the session identifier when available.

Workers return to the parent without further delegation unless explicitly assigned it. Ask them to report missing context or capabilities instead of inventing requirements.

## Choose An Execution Tool

- Read `~/Develop/dot-files/.ai/models.md` to select a worker. Prefer a native subagent when it supports the chosen model, tools, and scope; otherwise use an installed, authenticated agent CLI.
- Supported routes include `codex exec`, `claude -p`, Cursor Agent's `agent -p`, and Grok Build's `grok -p`. Other routes are eligible when their capabilities are verified. The Cursor editor's `cursor` command is not evidence that Cursor Agent CLI is installed.
- On first use of a route in the session, check its installed help, model-selection mechanism, workspace option, output format, and permission controls. Use exact model IDs for that route. Treat prompts as data: pass briefs via stdin or properly quoted arguments.
- Set the worker's working directory explicitly and provide the shared rules and relevant repository instructions. External CLI sessions may load different instructions, connectors, and permissions from the parent.
- Keep the worker within the parent's authorized scope and restrictions. Prefer read-only controls for investigation/review; use the host's approval mechanism when needed. Do not bypass a denied action by changing agents or tools.
- Capture output and the process/session identifier. Resume the specific worker by that identifier, not a global “last session” selector.

## Coordinate And Verify

- Parallelize independent work where it helps. Assign disjoint write ownership; use separate worktrees when edits, Git state, or test/build artifacts can interfere. Sequence work when isolation would cost more than it saves.
- Keep branch changes, commits, pushes, and integration with the parent unless explicitly assigned. All Git operations follow `git-workflow.md` in the canonical `.ai` directory.
- Avoid duplicating a worker's assignment while it runs. Do independent work or wait; collect required results before making dependent decisions.
- Review actual diffs and source evidence against the brief. Reuse valid test evidence, run missing checks, and recheck affected behavior after integration changes.
- For an independent review, supply the spec and diff and ask for evidence-backed findings. A different model/provider is optional, not proof of correctness.
- If a worker fails, inspect its output and partial changes before retrying. Correct the brief, execution problem, or model choice; after repeated failure, reassess the approach instead of launching the same task again.
- If a route is unavailable, disclose a suitable substitution or continue directly when feasible. Honor explicit user model/tool constraints. Report remaining gaps without claiming completion.
