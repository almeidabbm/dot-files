---
name: delegation
description: Spawn a worker agent (investigator, implementer, reviewer) on Anthropic or OpenAI from any host, choosing model and effort per assignment, with the brief template and result verification. Load when delegating a bounded investigation, a parallel implementation, or an independent review, and when the user names a worker model, provider, or effort.
---

# Delegation

Keep the main conversation on the user's goal and decisions. Workers return evidence, not their exploration logs.

## Workers

Three roles exist everywhere. Source: `.ai/agents/roles/` in dot-files, rendered by `.ai/agents/render.sh` into each host's agents directory and linked to `~/.agents/roles/<role>.md` for CLI briefs. A role carries instructions and write access only; provider, model, and effort are your decision on every spawn.

| Role | Assignment | Writes |
| --- | --- | --- |
| `investigator` | Trace code paths, gather evidence, answer one bounded question | No |
| `implementer` | Build a specified change with tests in an assigned scope | Yes |
| `reviewer` | Check a diff against its spec, return evidence-backed findings | No |

## Choose Provider, Model, And Effort

Every spawn states a role, a provider, a model, and an effort. The host you run in does not decide the worker's provider: Claude Code can run OpenAI workers and Codex can run Anthropic workers through the CLIs below. Inheriting your own model is the most expensive outcome and must be a stated choice, never an omission. Name role, provider, model, effort, and reason in a progress update.

Match the model to the assignment, not to the role:

| Assignment shape | Anthropic | OpenAI |
| --- | --- | --- |
| Narrow, repeatable transformation; mechanical search | `claude-haiku-4-5-20251001` | `gpt-5.6-luna` |
| Well-specified implementation or investigation | `sonnet` | `gpt-5.6-terra` |
| Ambiguous reasoning, hard debugging, consequential review | `opus` | `gpt-5.6-sol` |
| Most demanding assignments, or after a stronger attempt failed | `fable` | `gpt-6-astra` |

- Effort levels: Anthropic `low`, `medium`, `high`, `xhigh`, `max`; OpenAI `low`, `medium`, `high`, `xhigh`, `ultra`. Names are not equivalent across providers. Start at the model's default; raise effort or step up one row when the first attempt fails or the assignment turns out harder than briefed; step down when a task proves mechanical.
- Prefer the native route (same provider as the host) when both providers fit: it is cheaper to run and inherits the host's permissions. Cross the provider line when the other model fits better, when the user asks, or for an independent review by a different model. A different provider is optional, not proof of correctness.
- Honor the user's explicit model, tool, quality, speed, and usage preferences. Keep overrides scoped to the invocation; the table above is the only default, and changing them is a reviewable edit.
- Record the requested model and the actual model when the tool reports it. Aliases resolve differently per host and account: on 2026-09-09 `claude -p --model haiku` ran Sonnet 5 while the full Haiku id ran Haiku, so pass a full id when the choice matters and check `modelUsage` in the JSON result. The table is a routing hypothesis checked on 2026-09-09 against the [Claude Code model docs](https://code.claude.com/docs/en/model-config) and [Codex model docs](https://developers.openai.com/codex/models), not proof of access.

## Decide

- Keep work local when it is small, depends on continuous shared reasoning, or cannot be separated without extensive coordination. A fixed spec, implementation, review pipeline is unnecessary.
- Delegate independent investigation, a defined implementation, or a focused review.
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

OpenAI worker from any host (role instructions prepended from the linked role file):

```bash
cat ~/.agents/roles/<role>.md <brief-file> | codex exec - \
  -C <workdir> -m <model> -c model_reasoning_effort=<effort> \
  -s <read-only|workspace-write> --json -o <last-message-file>
```

The first JSONL event, `thread.started`, carries `thread_id`; the final message lands in the `-o` file. Resume with `codex exec resume <thread_id> - < <follow-up-file>`.

Anthropic worker from any host (the role comes from `~/.claude/agents/<role>.md`, installed by `link-claude.sh`, so that script must have run on this machine even when the host is Codex or OpenCode):

```bash
cd <workdir> && claude -p --agent <role> --model <model> --effort <effort> \
  --permission-mode <plan|acceptEdits> --output-format json < <brief-file>
```

The JSON result carries `session_id`; resume with `claude -p --resume <session_id> < <follow-up-file>`. Use `plan` for read-only roles and `acceptEdits` for the implementer.

- Keep the worker inside the parent's authorized scope. A denied action stays denied across agents, providers, and tools; use the host's approval mechanism instead of a bypass flag.
- Other installed agent CLIs (`cursor-agent -p`, `grok -p`) are eligible after reading their help for model selection, working directory, output format, and permissions. They are not part of the default routes.
- If a route or model is unavailable, distinguish model access from authentication, permissions, and task failure. Disclose the substitution or continue directly, and report remaining gaps without claiming completion.

## Coordinate And Verify

- Parallelize independent work. Assign disjoint write ownership; use separate worktrees when edits, Git state, or build artifacts can interfere. Sequence work when isolation would cost more than it saves.
- Keep branch changes, commits, pushes, and integration with the parent unless explicitly assigned. Git operations follow the `git-workflow` skill.
- Do independent work or wait while a worker runs; collect required results before dependent decisions.
- Review actual diffs and source evidence against the brief. Reuse valid test evidence, run missing checks, and recheck affected behavior after integration.
- For an independent review, supply the spec and diff and ask for evidence-backed findings.
- If a worker fails, inspect its output and partial changes before retrying. Correct the brief, execution problem, model, or effort; after repeated failure, reassess the approach instead of relaunching the same task.
