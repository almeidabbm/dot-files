# Worker Model Selection

Read when selecting a worker. Choose both a model and an execution tool; this file does not select or depend on the main agent's model.

## Selection Policy

- Honor the user's explicit model, tool, quality, speed, and usage preferences.
- Match capability to the assignment: uncertainty, context required, available tools, and how easily the result can be checked. Include the cost of briefing, retries, and integration when deciding whether delegation helps.
- Use a balanced model for a well-specified implementation or investigation; a faster model for narrow, repeatable transformations; a stronger model for ambiguous reasoning, difficult debugging, or consequential review.
- Start with the model's default effort. Increase supported effort or capability when the task or observed failure warrants it. Effort names are not equivalent across tools.
- Among suitable routes, prefer one already available and authenticated. Use relevant results from similar work over assumptions about which provider is “best.”
- Resolve availability when needed. A published model name or cached entry does not prove account access. If a launch fails, distinguish model availability from authentication, permissions, and task failures; disclose substitutions.
- Keep model choices scoped to the worker invocation. Changes to persistent defaults or this catalog are explicit, reviewable changes.

## Starting Candidates

Documentation checked 2026-09-08. These are routing hypotheses, not a benchmark or a guarantee of availability. Recheck official documentation when an entry is unavailable or stale.

| Intended work | Codex model ID | Claude Code alias |
| --- | --- | --- |
| Narrow, repeatable tasks | `gpt-5.6-luna` | `haiku` |
| Well-scoped implementation and investigation | `gpt-5.6-terra` | `sonnet` |
| Difficult reasoning, changes, or review | `gpt-5.6-sol` | `opus` |
| Most demanding assignments | `gpt-6-astra` | `fable` |

Entries in the same row are candidates, not equivalent models. Claude aliases can resolve differently by provider or configuration. Record the requested model and the actual model when the tool reports it; do not assume an alias resolved to a particular version.

## Other Execution Routes

- **Native subagents:** use the host's exposed models and tools. Select the worker model explicitly when supported; inherited defaults may be more expensive than the task needs.
- **Cursor Agent:** use `agent models` or the installed CLI's documented equivalent to discover account model IDs. Classify the selected model by its capabilities, not by the Cursor name. Use an explicit model if deterministic selection matters; an automatic router delegates that choice to Cursor.
- **Grok Build:** use `grok models` and current official model guidance. Add a task preference once supported by documentation or observed results; there is no assumed Grok-specific role.
- A model available in one tool is not necessarily available in another, and access to a model does not imply access to the same tools or connectors.

## Sources And Maintenance

- [OpenAI model guidance](https://developers.openai.com/codex/models)
- [Claude Code model configuration](https://code.claude.com/docs/en/model-config)
- [Cursor Agent parameters and model discovery](https://cursor.com/docs/cli/reference/parameters)
- [Grok Build CLI reference](https://docs.x.ai/build/cli/reference)

Tune preferences using representative tasks and record correctness, verification gaps, retries, elapsed time, and usage when available. Keep changes that improve the workflow; avoid generalizing from one success or failure.
