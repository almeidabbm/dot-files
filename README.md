# dot-files

> Shared configuration for shell, Neovim, Claude Code, Codex, and OpenCode — symlinked into `$HOME` so everything stays version-controlled.

---

## Quick start

**Full setup** (shell + editor + AI tooling):

```bash
git clone <repo-url> ~/Develop/dot-files
~/Develop/dot-files/link.sh
```

**Claude Code only** (won't touch your shell or editor):

```bash
git clone <repo-url> ~/Develop/dot-files
~/Develop/dot-files/link-claude.sh
```

**Codex only** (won't touch your shell or editor):

```bash
git clone <repo-url> ~/Develop/dot-files
~/Develop/dot-files/link-codex.sh
```

> To undo, run `unlink.sh`, `unlink-claude.sh`, or `unlink-codex.sh` respectively.

---

## What's inside

### Claude Code

Claude uses the shared workflow rules from [`.ai/shared-instructions.md`](.ai/shared-instructions.md), symlinked into Claude's native `~/.claude/CLAUDE.md` location by `link-claude.sh`.

**Shared rules** enforce:

- Branch management with **Graphite CLI** (`gt`) — with plain-`git` fallbacks for machines that lack it
- **Git worktrees** inside the repo (`.worktrees/`, gitignored) for parallel work
- Auto-decomposition of features into **stacked PRs**
- **Conventional commits** and **scoped testing** (only runs tests for changed files)
- Per-task working memory at `.local/active/<slug>/` (gitignored) — see "AI-Native Engineering Workflow" below

**Plugins:**

- [superpowers](https://github.com/obra/superpowers) — TDD, debugging, brainstorming, worktree workflows, code review, and more (installed from the official marketplace via `link-claude.sh`)

**Shared repo workflow skills** live in [`.ai/skills/`](.ai/skills/) and are symlinked into Claude's native skills folder by `link-claude.sh`.

**Skills**:

| Command          | What it does                                                                                                                |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `/start-task`    | On-ramp for a new piece of work. Creates `.local/active/<slug>/` with 4 templated files and auto-detects task size.         |
| `/status`        | "Where was I?" — read-only view of every active task with status, size, and next-step suggestion.                           |
| `/pre-merge`     | Pre-merge confidence gate. Adversarial review + hardening checklist against spec, plan, system-map, and the diff.           |
| `/archive-task`  | Lifecycle close-out. Moves `active/<slug>/` → `archive/<slug>/`, optionally graduates spec/runbook to `docs/`.              |
| `/code-review`   | Reviews a PR or Graphite stack. Checks correctness, security, types, architecture. Composes with `/pre-merge`.              |

### Codex

Codex uses the same shared workflow rules from [`.ai/shared-instructions.md`](.ai/shared-instructions.md), symlinked into Codex's native `~/.codex/AGENTS.md` location by `link-codex.sh`.

**Shared repo workflow skills** live once in [`.ai/skills/`](.ai/skills/) and are symlinked into `~/.codex/skills/` by `link-codex.sh`.

| Skill            | What it does                                                                                                                |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `start-task`     | Creates `.local/active/<slug>/` with templated task files and detected size.                                               |
| `status`         | Summarizes active tasks and the next likely step.                                                                           |
| `pre-merge`      | Runs a production-safety gate against spec, plan, system-map, and diff.                                                    |
| `archive-task`   | Moves completed task memory into `archive/` and offers doc or system-map graduation.                                       |
| `code-review`    | Reviews a diff, branch, or PR for correctness, security, types, architecture, and tests.                                  |

**Plugin install:** `link-codex.sh` installs native Superpowers with `codex plugin add superpowers@openai-curated`.

If `superpowers` is installed in Codex, these task files are the integration point: `spec.md` and `plan.md` remain the source of truth for this workflow.

### OpenCode

OpenCode uses the same shared workflow rules from [`.ai/shared-instructions.md`](.ai/shared-instructions.md), symlinked into OpenCode's native `~/.config/opencode/AGENTS.md` location by `link-opencode.sh`.

**Shared repo workflow skills** live once in [`.ai/skills/`](.ai/skills/) and are symlinked into `~/.config/opencode/skills/` by `link-opencode.sh`.

**Plugin install:** `link-opencode.sh` clones [superpowers](https://github.com/obra/superpowers) into `~/.config/opencode/superpowers` and symlinks its plugin and skills into OpenCode.

### Shared Source

The reusable workflow content is agent-agnostic and lives in:

- [`.ai/shared-instructions.md`](.ai/shared-instructions.md) for durable global workflow rules
- [`.ai/skills/`](.ai/skills/) for reusable task workflows

The link scripts project those shared files into each tool's native structure:

- Claude Code -> `~/.claude/CLAUDE.md` and `~/.claude/skills/`
- Codex -> `~/.codex/AGENTS.md` and `~/.codex/skills/`
- OpenCode -> `~/.config/opencode/AGENTS.md` and `~/.config/opencode/skills/`

---

### AI-Native Engineering Workflow

These shared skills plus the shared instructions file form a small workflow layer on top of Superpowers. In Claude, the user-facing surface is three commands (`/start-task`, `/pre-merge`, `/archive-task`) plus `/status`; in Codex, the same workflows are available as skills.

**Per-task working memory** at `.local/active/<slug>/`:

- `spec.md` — written by `superpowers:brainstorming`
- `plan.md` — written by `superpowers:writing-plans`
- `notes.md` — front-matter (slug, linear, size, status, last-updated) + running log
- `review.md` — written by `/pre-merge`

**Durable architectural intelligence** at `.local/system-map/` (prefixed filenames: `inv-`, `area-`, `danger-`, `pitfall-`). Grows as tasks archive.

**Typical flow:**

1. `/start-task` (slug + auto-detected size) →
2. describe intent — Claude picks brainstorming, writing-plans, TDD as appropriate →
3. `/pre-merge` when tests pass →
4. submit + merge →
5. `/archive-task` (auto-suggested when PR is merged).

See the design spec at `.local/active/2026-05-24-ai-native-eng-os/spec.md` (gitignored — read locally) for the full design.

---

### Neovim

Simplified Neovim 0.11 config with [lazy.nvim](https://github.com/folke/lazy.nvim). Optimized for TypeScript/JavaScript web development.

|                |                                                                                         |
| -------------- | --------------------------------------------------------------------------------------- |
| **LSP**        | ts_ls, eslint, html, cssls, jsonls, yamlls, dockerls, lua_ls (auto-installed via Mason) |
| **Completion** | Neovim 0.11 native LSP completion                                                      |
| **Navigation** | Telescope (fuzzy finder) + Harpoon 2 (file marks)                                       |
| **Git**        | Gitsigns + Diffview (diffs) + git-conflict (merge resolution)                           |
| **AI**         | claudecode.nvim + opencode.nvim (AI CLI integrations)                                   |
| **Buffers**    | Bufferline (buffer tabs with pin/close support)                                         |
| **Formatting** | conform.nvim (oxfmt > prettier for JS/TS, stylua for Lua)                               |
| **Theme**      | Kanagawa (wave)                                                                         |
| **Leader**     | `Space`                                                                                 |

Full keybindings in [`.config/nvim/KEYBINDINGS.md`](.config/nvim/KEYBINDINGS.md).

---

### Shell

Zsh with [oh-my-zsh](https://ohmyz.sh/) + [powerlevel10k](https://github.com/romkatv/powerlevel10k) prompt. Includes git and [asdf](https://asdf-vm.com/) plugins, [fzf](https://github.com/junegunn/fzf) integration, Go path setup, and bun completions.

---

## Scripts

| Script             | Purpose                                        |
| ------------------ | ---------------------------------------------- |
| `link.sh`          | Symlink everything into `$HOME`                |
| `unlink.sh`        | Remove all symlinks managed by this repo       |
| `link-claude.sh`   | Symlink only Claude Code config                |
| `unlink-claude.sh` | Remove only Claude Code symlinks               |
| `link-codex.sh`    | Symlink only Codex config                      |
| `unlink-codex.sh`  | Remove only Codex symlinks                     |
| `link-opencode.sh` | Symlink only OpenCode config                   |
| `unlink-opencode.sh` | Remove only OpenCode symlinks                |
| `list-symlink.sh`  | List all active symlinks pointing to this repo |

## Prerequisites

| Tool                                                          | Required for            |
| ------------------------------------------------------------- | ----------------------- |
| [Neovim](https://neovim.io/) >= 0.11                          | Editor config           |
| [oh-my-zsh](https://ohmyz.sh/)                                | Shell config            |
| [powerlevel10k](https://github.com/romkatv/powerlevel10k)     | Shell theme             |
| [asdf](https://asdf-vm.com/)                                  | Version management      |
| [fzf](https://github.com/junegunn/fzf)                        | Fuzzy finding           |
| [Graphite CLI](https://graphite.dev/docs/graphite-cli)        | Shared workflow rules   |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Claude integration      |
| [Codex](https://developers.openai.com/codex/)                 | Codex integration       |
