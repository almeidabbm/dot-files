# dot-files

> Shared configuration for shell, Neovim, Claude Code, Codex, and OpenCode — symlinked into `$HOME` so everything stays version-controlled.

---

## Quick start

New machine? [`docs/SETUP.md`](docs/SETUP.md) walks through git, GitHub, and stacked PRs.

```bash
git clone <repo-url> ~/Develop/dot-files
~/Develop/dot-files/link.sh          # everything
```

Each piece installs on its own if you'd rather not touch your shell or editor:

| Install | Remove | What it touches |
| --- | --- | --- |
| `link.sh` | `unlink.sh` | Everything below |
| `link-claude.sh` | `unlink-claude.sh` | `~/.claude/` |
| `link-codex.sh` | `unlink-codex.sh` | `~/.codex/` |
| `link-opencode.sh` | `unlink-opencode.sh` | `~/.config/opencode/` |

Check an install with `./doctor.sh` (read-only, exits non-zero on the first dangling link) or `./list-symlink.sh`.

---

## Shared AI rules

Operating rules for agents live under [`.ai/`](.ai/) and are projected into each tool's native path by the `link-*.sh` scripts. One source, three hosts:

| What | Source | Claude Code | Codex | OpenCode |
| --- | --- | --- | --- | --- |
| Always-loaded rules | [`shared-instructions.md`](.ai/shared-instructions.md) | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` | `~/.config/opencode/AGENTS.md` |
| On-demand skills | [`skills/`](.ai/skills/) | `~/.claude/skills/` | `~/.agents/skills/` | `~/.agents/skills/` |
| Worker agents | [`agents/roles/`](.ai/agents/roles/) | `~/.claude/agents/` | `~/.codex/agents/` | `~/.config/opencode/agents/` |

The always-loaded file holds task, verification, and style rules plus one-line hooks into the skills. Each host lists skill descriptions every turn and loads the body on demand, which is far more reliable than a "read this path" pointer:

| Skill | Fires when |
| --- | --- |
| [`git-workflow`](.ai/skills/git-workflow/SKILL.md) | First branch, commit, stack, worktree, or PR operation in a task; `gh stack` or a rebase fails |
| [`delegation`](.ai/skills/delegation/SKILL.md) | Delegating a bounded investigation, parallel implementation, or independent review; choosing a worker's provider, model, or effort |

Three worker roles (`investigator`, `implementer`, `reviewer`) are written once in [`agents/roles/`](.ai/agents/roles/) and rendered into each host's agent format by [`agents/render.sh`](.ai/agents/render.sh); run it after editing a role, and `doctor.sh` fails when the rendered files are stale. A role fixes instructions and write access only. The main agent chooses provider, model, and effort per spawn, and can run a worker on either provider from any host: native subagents for the host's own provider, `codex exec` or `claude -p` for the other one. The role text is also linked at `~/.agents/roles/` so a CLI brief can prepend it.

Start your preferred agent normally. The workflow does not depend on the main agent's model or require a custom launcher. Paths assume `~/Develop/dot-files`, matching the install scripts. This layer instructs agents; it does not enforce against them. Branch policy belongs to each repository.

For Cursor Agent chat, add this pointer to **User Rules** in Cursor's rules settings:

```text
At the start of each task, read and follow ~/Develop/dot-files/.ai/shared-instructions.md.
```

Cursor's global User Rules apply to Agent chat, not Tab or inline editing ([Cursor rules](https://cursor.com/docs/rules)). The `link-*.sh` scripts install rules for the three tools in the table; they do not configure Cursor or Grok.

The [research and audit notes](docs/ai-workflow-research.md) record the evidence, including the transcript measurement that motivated moving procedures into skills. To evaluate a rule change, use a small direct edit, an independent investigation, and a scoped implementation/review task, and check whether the skill actually loaded and which worker, provider, and model were chosen.

---

## Neovim

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

## tmux

Stock tmux with comfort settings only — every default key binding is left alone,
so what you learn transfers to any machine. Mouse on, 50k lines of scrollback, Kanagawa status bar to match Neovim.

Keys and a troubleshooting table in [`.config/tmux/CHEATSHEET.md`](.config/tmux/CHEATSHEET.md).

## Shell

Zsh with [oh-my-zsh](https://ohmyz.sh/) + [powerlevel10k](https://github.com/romkatv/powerlevel10k) prompt. Includes git and [asdf](https://asdf-vm.com/) plugins, [fzf](https://github.com/junegunn/fzf) integration, Go path setup, and bun completions.

## Prerequisites

| Tool | Required for |
| --- | --- |
| [Neovim](https://neovim.io/) >= 0.11 | Editor config |
| [oh-my-zsh](https://ohmyz.sh/) | Shell config |
| [powerlevel10k](https://github.com/romkatv/powerlevel10k) | Shell theme |
| [asdf](https://asdf-vm.com/) | Version management |
| [fzf](https://github.com/junegunn/fzf) | Fuzzy finding |
| [tmux](https://github.com/tmux/tmux) | Terminal multiplexing |
| [GitHub CLI](https://cli.github.com/) + `gh stack` | Shared stacking rules |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Claude integration |
| [Codex](https://developers.openai.com/codex/) | Codex integration |
