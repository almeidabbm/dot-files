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

**Skills** — slash commands you can use inside Claude Code:

| Command           | What it does                                                                                                                       |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `/worktree-setup` | Creates a git worktree, builds a Graphite stack inside it, does the work, and cleans up when done. Use this to start any new task. |
| `/code-review`    | Reviews a PR or Graphite stack. Checks correctness, security, types, architecture. Can submit the review via GitHub.               |
| `/review-respond` | Fetches outstanding review comments, applies fixes with `gt modify`, restacks, and verifies nothing broke.                         |

---

### Neovim

Lua-based config with [lazy.nvim](https://github.com/folke/lazy.nvim). Optimized for TypeScript/JavaScript web development.

|                |                                                                                         |
| -------------- | --------------------------------------------------------------------------------------- |
| **LSP**        | ts_ls, eslint, html, cssls, jsonls, yamlls, dockerls, lua_ls (auto-installed via Mason) |
| **Completion** | nvim-cmp with LSP, buffer, path, and snippet sources                                    |
| **Navigation** | Telescope (fuzzy finder) + nvim-tree (file explorer)                                    |
| **Theme**      | Dracula                                                                                 |
| **Leader**     | `;`                                                                                     |

Full keybindings and plugin list in [`.config/nvim/README.md`](.config/nvim/README.md).

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
| [Neovim](https://neovim.io/) >= 0.9                           | Editor config           |
| [oh-my-zsh](https://ohmyz.sh/)                                | Shell config            |
| [powerlevel10k](https://github.com/romkatv/powerlevel10k)     | Shell theme             |
| [asdf](https://asdf-vm.com/)                                  | Version management      |
| [fzf](https://github.com/junegunn/fzf)                        | Fuzzy finding           |
| [Graphite CLI](https://graphite.dev/docs/graphite-cli)        | Claude Code skills      |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Skills and global rules |
