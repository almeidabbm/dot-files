# dot-files

> Shared configuration for shell, Neovim, and Claude Code — symlinked into `$HOME` so everything stays version-controlled.

---

## Quick start

**Full setup** (shell + editor + Claude Code):

```bash
git clone <repo-url> ~/Develop/dot-files
~/Develop/dot-files/link.sh
```

**Claude Code only** (won't touch your shell or editor):

```bash
git clone <repo-url> ~/Develop/dot-files
~/Develop/dot-files/link-claude.sh
```

> To undo, run `unlink.sh` or `unlink-claude.sh` respectively.

---

## What's inside

### Claude Code

Custom global rules and slash commands that standardize how Claude Code works across all projects.

**Global rules** ([`CLAUDE.md`](.claude/CLAUDE.md)) enforce:

- Branch management with **Graphite CLI** (`gt`)
- **Git worktrees** for parallel work on separate tasks
- Auto-decomposition of features into **stacked PRs**
- **Conventional commits** and **scoped testing** (only runs tests for changed files)

**Plugins:**

- [superpowers](https://github.com/obra/superpowers) — TDD, debugging, brainstorming, worktree workflows, code review, and more (installed from the official marketplace via `link-claude.sh`)

**Skills** — custom slash commands:

| Command        | What it does                                                                                                         |
| -------------- | -------------------------------------------------------------------------------------------------------------------- |
| `/code-review` | Reviews a PR or Graphite stack. Checks correctness, security, types, architecture. Can submit the review via GitHub. |

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
| `list-symlink.sh`  | List all active symlinks pointing to this repo |

## Prerequisites

| Tool                                                          | Required for            |
| ------------------------------------------------------------- | ----------------------- |
| [Neovim](https://neovim.io/) >= 0.11                          | Editor config           |
| [oh-my-zsh](https://ohmyz.sh/)                                | Shell config            |
| [powerlevel10k](https://github.com/romkatv/powerlevel10k)     | Shell theme             |
| [asdf](https://asdf-vm.com/)                                  | Version management      |
| [fzf](https://github.com/junegunn/fzf)                        | Fuzzy finding           |
| [Graphite CLI](https://graphite.dev/docs/graphite-cli)        | Claude Code skills      |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Skills and global rules |
