# Neovim Configuration

A simplified Neovim 0.11 configuration focused on web development with AI integration.

## Features

- **Neovim 0.11 native completion** — no plugin needed, LSP-powered
- **Kanagawa** (wave) theme with matching statusline
- **Bufferline** for buffer tabs with pin and close-others support
- **Telescope** for fuzzy finding files, grep, buffers, and in-buffer search
- **Harpoon 2** for marking and jumping between key files
- **Diffview + git-conflict** for reviewing diffs and resolving merge conflicts
- **AI integration** via claudecode.nvim and opencode.nvim
- **conform.nvim** for formatting (oxfmt > prettier for JS/TS, stylua for Lua)
- **Treesitter** for syntax highlighting and text objects
- **Mason** for auto-installing LSP servers and formatters

## Keybindings

See [KEYBINDINGS.md](./KEYBINDINGS.md) for the full cheatsheet.

**Quick reference:** Press `Space` and wait — which-key shows all available bindings.

## Directory Structure

```
~/.config/nvim/
├── init.lua                  # Entry point, bootstrap lazy.nvim
├── KEYBINDINGS.md            # Full keybindings cheatsheet
├── lua/
│   ├── config/
│   │   ├── lazy.lua          # Plugin manager setup
│   │   ├── options.lua       # Neovim options/settings
│   │   └── keymaps.lua       # Global keymaps
│   └── plugins/
│       ├── ai.lua            # Claude Code integration
│       ├── editor.lua        # Treesitter, Telescope, text objects
│       ├── formatting.lua    # conform.nvim (prettier, stylua)
│       ├── git.lua           # Gitsigns, Diffview, git-conflict
│       ├── lsp.lua           # LSP servers and configuration
│       ├── navigation.lua    # Harpoon file navigation
│       └── ui.lua            # Theme, statusline, which-key, trouble
└── README.md
```

## Language Servers (auto-installed via Mason)

- **ts_ls** — TypeScript/JavaScript
- **eslint** — ESLint linting
- **html/cssls** — HTML and CSS
- **jsonls/yamlls** — JSON and YAML with schema validation
- **dockerls** — Dockerfile
- **lua_ls** — Lua (for Neovim config)

## Installation

This config is managed via the dotfiles repo symlink script:

```bash
cd ~/Develop/dot-files
./link.sh        # Symlinks nvim config to ~/.config/nvim
nvim             # Open nvim — plugins auto-install on first launch
```

Run `:checkhealth` after first launch to verify everything is working.
