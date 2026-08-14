# Harness

How the workflow layer is wired, and what to do when it misbehaves.

`shared-instructions.md` holds the operating rules. This file holds the
machinery those rules assume: where each concern lives, how the current task is
resolved, and how to recover a broken install. Read it when a rule's mechanism
matters — a binding is ambiguous, the guard blocked a command, `agent-memory`
is missing, or you are changing the harness itself.

## Three layers

| Layer | Source | Reaches the agent through |
| --- | --- | --- |
| **Projection** | `.ai/shared-instructions.md`, `.ai/skills/` | `link-*.sh` symlinks into each tool's native path |
| **Memory** | the resolved memory root | the `agent-memory` command |
| **Guard** | `.ai/hooks/guard-git-trunk.sh` | a `PreToolUse(Bash)` entry in `~/.claude/settings.json` |

Projection is one-way and identical per tool: `.ai/` is the source, the tool
paths are its image. Claude reads `~/.claude/CLAUDE.md` and `~/.claude/skills/`,
Codex reads `~/.codex/AGENTS.md` and `~/.codex/skills/`, OpenCode reads
`~/.config/opencode/`. All three resolve to the same files.

The guard is the exception: it is Claude-only, and it is *merged* into
`settings.json` with `jq` rather than symlinked, because that file also carries
Claude's own machine-local state.

## Change the source

| To change | Edit |
| --- | --- |
| Operating rules for every tool | `.ai/shared-instructions.md` |
| A workflow procedure | `.ai/skills/<name>/SKILL.md` |
| Trunk-guard behaviour | `.ai/hooks/guard-git-trunk.sh` |
| Task memory structure or CLI | `.ai/lib/agent_memory.py` (tests in `.ai/tests/`) |
| Which files get projected | the matching `link-*.sh` |

Editing a projected path (`~/.claude/CLAUDE.md`) writes through the symlink to
the repo file, so the change is version-controlled but the diff shows up
somewhere you did not expect. Prefer the repo path.

`~/.claude/settings.json` is machine-local. Only its guard-hook entry comes from
this repo; everything else there stays on the machine, so treat it as untracked
state.

## Memory root

Resolve it — never hard-code it:

```bash
agent-memory root --repo <checkout>     # honours AGENT_LOCAL_MEMORY_PATH
```

```text
<memory-root>/
  tasks/active/<slug>--<suffix>/     task.json spec.md plan.md notes.md review.md
  tasks/archive/<slug>--<suffix>/
  repositories/<repo-id>/            system map: inv- area- danger- pitfall-
  registry/bindings.json             checkout+branch -> task_id
  registry/repositories.json         canonical repository identities
  migrations/                        legacy-store migration reports
```

Task memory is task-centric, not checkout-centric: one task may bind several
repositories, and a repository may have several active tasks. That is why the
current task is *resolved*, not inferred.

## Resolving the current task

`agent-memory current --repo <checkout>` applies this order and stops at the
first hit:

1. **Explicit** — `--task <id-or-slug>`.
2. **Session** — the `AGENT_TASK_ID` environment variable. Export it to pin a
   shell, a worktree, or a sub-agent to one task.
3. **Binding, exact** — a `bindings.json` entry matching this repo identity,
   this checkout path, *and* the current branch. Most recent wins.
4. **Binding, checkout** — same repo identity and checkout, any branch.
5. **Manifest** — exactly one active task lists this repository. Two or more is
   an error, not a guess.

Modification time is never consulted. When the answer is ambiguous the CLI fails
and asks for an explicit bind:

```bash
agent-memory bind <task-id-or-slug> --repo <checkout> --branch <branch>
```

A worktree needs its own bind after creation — it is a different checkout path
than the main repo, so it inherits nothing.

## Guard behaviour

The hook reads the `PreToolUse` payload on stdin and exits `2` to block, with
the reason on stderr. It blocks exactly two things:

- `git commit` while the current branch is `main`, `master`, or `trunk`
- `git push` from a trunk branch, or with a refspec whose destination is trunk

Matching is exact, so `main-feature` and `feature/main-nav` pass. Feature
commits, feature pushes, and PR submits all pass.

It fails open. Without `jq`, or with an unreadable payload, it exits `0` and
allows the command — the guard never bricks git.

When it blocks you, the branch is wrong, not the guard. Create a feature branch
and retry.

## Recovery

**`agent-memory: command not found`** — run `./link-agent-memory.sh`. It links
`.ai/bin/agent-memory` to `~/.local/bin/agent-memory`. Do not fall back to a
repository-local `.local/` directory; that is the legacy layout tasks moved off.

**"multiple active tasks match this repository"** — bind explicitly (above), or
pass `--task` for one command.

**"no active task is bound to this repository"** — either attach the repository
to an existing task with `agent-memory add-repo <task> --repo <checkout> --role
<role>`, or start a new one.

**Skills missing after an update** — re-run the tool's link script; `link.sh`
does all of them. Verify with `./doctor.sh`, which is read-only and exits
non-zero on the first dangling link.

**`.migration.lock` left behind by a crash** — confirm no migration is running,
remove only that lock directory from the resolved memory root, and rerun the
same command. A normal failure removes its own lock.

## Verifying a change

```bash
python3 -m unittest discover -s .ai/tests   # agent-memory CLI
./doctor.sh                                 # symlinks resolve
```

Both are safe to run repeatedly and neither touches task memory.
