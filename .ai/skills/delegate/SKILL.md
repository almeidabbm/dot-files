---
name: delegate
description: Spawn a worker agent (investigator, implementer, reviewer) through the host's native subagents or another agent CLI, choosing provider, model, and effort per assignment, with the brief template and result verification. Load when delegating a bounded investigation, a parallel implementation, or an independent review, and when the user names a worker model, provider, or effort.
---

# Delegate

Keep the main conversation on the user's goal and decisions. Workers return evidence, not their exploration logs.

## Workers

Three roles are installed as each host's native agents, and their plain instructions live at `~/.agents/roles/<role>.md` for CLI briefs. A role carries instructions and write access only; provider, model, and effort are your decision on every spawn.

| Role | Assignment | Writes |
| --- | --- | --- |
| `investigator` | Trace code paths, gather evidence, answer one bounded question | No |
| `implementer` | Build a specified change with tests in an assigned scope | Yes |
| `reviewer` | Check a diff against its spec, return evidence-backed findings | No |

## Choose Provider, Model, And Effort

Choose the role and provider for the assignment, using models and effort levels supported by the current host or CLI. Honor the user's explicit model, tool, quality, speed, and usage preferences. Select from current availability rather than a model list cached in this skill.

- Match capability and cost to the task. Use the model's default effort unless the assignment warrants an override; increase effort or capability when evidence shows the first choice was insufficient.
- Prefer the native route when both providers fit. Use another provider when it better fits the assignment or the user requests it. An independent review does not require a different provider.
- Check the actual model when the tool reports it; aliases can resolve differently across hosts and accounts. Use an exact model ID when that distinction matters.
- Briefly explain what is delegated and why. Mention model and effort only when requested or when the choice involves a meaningful tradeoff.

## Decide

- Delegate only when the subtask is independent and its benefit exceeds the cost of briefing, coordinating, and verifying it. A bounded investigation or a review before a PR is a candidate, not an automatic delegation step.
- When the assignment is to draft a specification, give an `investigator` the problem and open questions; give an `implementer` the agreed behavior and acceptance criteria. Keep unresolved product decisions visible to the user.

## Brief

Workers start without conversation history, tools, or skills unless the brief provides them. Every brief includes:

1. **Role and goal:** the bounded objective and what is outside scope.
2. **Context:** relevant decisions, file or source references, applicable skill names, and necessary facts from the conversation.
3. **Workspace and ownership:** exact repository or worktree directory, allowed edits or read-only, and whether Git actions are assigned.
4. **Done when:** observable acceptance criteria and the verification commands where known.
5. **Return:** findings or changes with file references, checks actually run with their results, unresolved issues, and the session identifier when available.

Workers return to the parent without further delegation unless assigned it. Ask them to report missing context or capabilities instead of inventing requirements. Treat the brief as data: write it to a file and pipe it on stdin, never interpolate it into a shell string.

## Run

| Host | Worker provider | Route |
| --- | --- | --- |
| Claude Code | Anthropic | Agent tool with `subagent_type: <role>` and `model: <model>`. Effort is not a per-call argument; when it matters, use the `claude -p` route below. |
| Claude Code | OpenAI | `codex exec` below |
| Codex | OpenAI | Native spawn: name the role, model, and reasoning effort in the spawn request. |
| Codex | Anthropic | `claude -p` below |
| OpenCode | Anthropic or OpenAI | Subagents inherit the primary agent's model with no per-spawn choice. Use the CLIs below for any explicit model or effort. |

`codex exec` route, usable from any host (role instructions prepended from `~/.agents/roles/<role>.md`):

```bash
cat ~/.agents/roles/<role>.md <brief-file> | codex exec - \
  -C <workdir> -m <model> -c model_reasoning_effort=<effort> \
  -s <read-only|workspace-write> --json -o <last-message-file>
```

The first JSONL event, `thread.started`, carries `thread_id`; the final message lands in the `-o` file. Resume with `codex exec resume <thread_id> - < <follow-up-file>`.

`claude -p` route, usable from any host (the role comes from `~/.claude/agents/<role>.md`, which must exist even when the host is not Claude Code):

```bash
cd <workdir> && claude -p --agent <role> --model <model> --effort <effort> \
  --permission-mode <plan|acceptEdits> --output-format json < <brief-file>
```

The JSON result carries `session_id`; resume with `claude -p --resume <session_id> < <follow-up-file>`. Use `plan` for read-only roles and `acceptEdits` for the implementer.

- Keep the worker inside the parent's authorized scope. A denied action stays denied across agents, providers, and tools; use the host's approval mechanism instead of a bypass flag.
- Other installed agent CLIs (`cursor-agent -p`, `grok -p`) are eligible after reading their help for model selection, working directory, output format, and permissions. They are not part of the default routes.
- If a role file a route needs is missing, report it instead of improvising the role. If a route or model is unavailable, distinguish model access from authentication, permissions, and task failure. Disclose the substitution or continue directly, and report remaining gaps without claiming completion.

## Coordinate And Verify

- Parallelize independent work. Assign disjoint write ownership; use separate worktrees when edits, Git state, or build artifacts can interfere. Sequence work when isolation would cost more than it saves.
- Keep branch changes, commits, pushes, and integration with the parent unless explicitly assigned. Git operations follow the `git-workflow` skill.
- Do independent work or wait while a worker runs; collect required results before dependent decisions.
- Review actual diffs and source evidence against the brief. Reuse valid test evidence, run missing checks, and recheck affected behavior after integration.
- For an independent review, supply the spec and diff and ask for evidence-backed findings.
- If a worker fails, inspect its output and partial changes before retrying. Correct the brief, execution problem, model, or effort; after repeated failure, reassess the approach instead of relaunching the same task.
