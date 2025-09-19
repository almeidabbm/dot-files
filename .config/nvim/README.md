# Neovim Configuration

A clean, modern Neovim configuration focused on web development (JS/TS/JSON/HTML/CSS) with Docker and YAML support.

## Features

-   **Modern Plugin Manager**: Lazy.nvim for fast startup and plugin management
-   **Language Support**: TypeScript, JavaScript, JSON, HTML, CSS, Docker, YAML, Lua
-   **Smart Completion**: nvim-cmp with LSP, buffer, path, and snippet sources
-   **File Navigation**: Telescope for fuzzy finding, nvim-tree for file explorer
-   **Git Integration**: Gitsigns for git hunks, blame, and diff
-   **Theme**: Dracula colorscheme with matching statusline
-   **Quality of Life**: Auto-pairs, commenting, surround, better escape

## Directory Structure

```
~/.config/nvim/
├── init.lua                    # Entry point, bootstrap lazy.nvim
├── lua/
│   ├── config/
│   │   ├── lazy.lua           # Plugin manager setup
│   │   ├── options.lua        # Neovim options/settings
│   │   └── keymaps.lua        # Global keymaps
│   └── plugins/
│       ├── completion.lua     # nvim-cmp and snippet setup
│       ├── dashboard.lua      # Alpha startup screen
│       ├── editor.lua         # Treesitter, Telescope, text objects
│       ├── filetree.lua       # nvim-tree file explorer
│       ├── formatting.lua     # null-ls, prettier, stylua
│       ├── lsp.lua           # LSP servers and configuration
│       └── ui.lua            # Theme, statusline, which-key, gitsigns
└── README.md                  # This file
```

## Plugins Installed

### Core

-   **[lazy.nvim](https://github.com/folke/lazy.nvim)**: Plugin manager
-   **[which-key.nvim](https://github.com/folke/which-key.nvim)**: Key binding help

### Theme & UI

-   **[dracula.nvim](https://github.com/Mofiqul/dracula.nvim)**: Dracula colorscheme
-   **[lualine.nvim](https://github.com/nvim-lualine/lualine.nvim)**: Statusline
-   **[alpha-nvim](https://github.com/goolord/alpha-nvim)**: Startup dashboard
-   **[indent-blankline.nvim](https://github.com/lukas-reineke/indent-blankline.nvim)**: Indent guides

### Editor

-   **[nvim-treesitter](https://github.com/nvim-treesitter/nvim-treesitter)**: Syntax highlighting
-   **[telescope.nvim](https://github.com/nvim-telescope/telescope.nvim)**: Fuzzy finder
-   **[nvim-tree.lua](https://github.com/nvim-tree/nvim-tree.lua)**: File explorer
-   **[trouble.nvim](https://github.com/folke/trouble.nvim)**: Diagnostics UI

### Completion & LSP

-   **[nvim-lspconfig](https://github.com/neovim/nvim-lspconfig)**: LSP configuration
-   **[mason.nvim](https://github.com/williamboman/mason.nvim)**: LSP/tool installer
-   **[nvim-cmp](https://github.com/hrsh7th/nvim-cmp)**: Completion engine
-   **[LuaSnip](https://github.com/L3MON4D3/LuaSnip)**: Snippet engine

### Formatting & Linting

-   **[none-ls.nvim](https://github.com/nvimtools/none-ls.nvim)**: Formatter/linter integration
-   **[mason-null-ls.nvim](https://github.com/jay-babu/mason-null-ls.nvim)**: Mason integration

### Text Editing

-   **[nvim-autopairs](https://github.com/windwp/nvim-autopairs)**: Auto-close brackets
-   **[Comment.nvim](https://github.com/numToStr/Comment.nvim)**: Smart commenting
-   **[nvim-surround](https://github.com/kylechui/nvim-surround)**: Surround text objects
-   **[better-escape.nvim](https://github.com/max397574/better-escape.nvim)**: Better escape sequences

### Git

-   **[gitsigns.nvim](https://github.com/lewis6991/gitsigns.nvim)**: Git hunks, blame, and diff

## Language Servers

Automatically installed via Mason:

-   **ts_ls**: TypeScript/JavaScript
-   **eslint**: ESLint linting
-   **html**: HTML
-   **cssls**: CSS
-   **jsonls**: JSON with schema validation
-   **yamlls**: YAML with schema validation
-   **dockerls**: Dockerfile
-   **lua_ls**: Lua (for Neovim configuration)

## Formatters

Automatically installed via Mason:

-   **prettier**: JavaScript, TypeScript, JSON, HTML, CSS, YAML, Markdown
-   **stylua**: Lua formatting

## Key Mappings

### Leader Key

-   Leader key: `;`

### File Navigation & Search

-   `<leader>ft`: Toggle file tree
-   `<leader>fe`: Focus file tree
-   `<leader>fF`: Find current file in tree
-   `<leader>ff`: Find files
-   `<leader>fg`: Live grep (search in files)
-   `<leader>fr`: Recent files
-   `<leader>fb`: Open buffers
-   `<leader>fh`: Help tags
-   `<leader>fd`: Search diagnostics

### LSP

-   `gd`: Go to definition
-   `gy`: Go to type definition
-   `gi`: Go to implementation
-   `gr`: Go to references
-   `K`: Show hover information
-   `<leader>lr`: Rename symbol
-   `<leader>la`: Code actions
-   `[g` / `]g`: Previous/next diagnostic
-   `<leader>lf`: Format buffer
-   `<leader>ld`: Show line diagnostics

### Git

-   `<leader>gf`: Git files (Telescope)
-   `<leader>gs`: Git status (Telescope)
-   `]h` / `[h`: Next/previous hunk
-   `<leader>ghs`: Stage hunk
-   `<leader>ghr`: Reset hunk
-   `<leader>ghS`: Stage buffer
-   `<leader>ghu`: Undo stage hunk
-   `<leader>ghR`: Reset buffer
-   `<leader>ghp`: Preview hunk
-   `<leader>ghb`: Blame line
-   `<leader>ghd`: Diff this

### Window Management

-   `<C-h/j/k/l>`: Navigate windows
-   `<C-Up/Down/Left/Right>`: Resize windows
-   `<leader>w-`: Split window horizontally
-   `<leader>w|`: Split window vertically
-   `<leader>wd`: Delete window
-   `<leader>ww`: Other window

### Tabs

-   `<leader><tab><tab>`: New tab
-   `<leader><tab>d`: Close tab
-   `<leader><tab>]` / `<leader><tab>[`: Next/previous tab
-   `<leader><tab>f` / `<leader><tab>l`: First/last tab

### Text Editing

-   `<A-j/k>`: Move line up/down (normal mode)
-   `<A-j/k>`: Move selection up/down (visual mode)
-   `</>>`: Indent left/right and stay in visual mode
-   `<C-s>`: Save file
-   `<C-d/u>zz`: Scroll and center cursor
-   `<esc>`: Clear search highlights
-   `jk` / `jj`: Escape to normal mode (insert mode)

### Diagnostics/Trouble

-   `<leader>xx`: Toggle Trouble
-   `<leader>xw`: Workspace diagnostics
-   `<leader>xd`: Document diagnostics
-   `<leader>xq`: Quickfix
-   `<leader>xl`: Location list

### Completion (Insert Mode)

-   `<Tab>`: Next completion item or expand snippet
-   `<S-Tab>`: Previous completion item or jump back in snippet
-   `<C-Space>`: Trigger completion
-   `<C-e>`: Abort completion
-   `<CR>`: Confirm completion
-   `<C-b/f>`: Scroll completion docs

## Dashboard Commands

When starting Neovim without a file:

-   `f`: Find file
-   `e`: New file
-   `r`: Recently used files
-   `t`: Find text
-   `c`: Open configuration
-   `q`: Quit Neovim

## Custom Settings

### Options

-   Line numbers with relative numbers
-   2-space indentation (tabs expanded to spaces)
-   Smart case-insensitive search
-   True color support
-   System clipboard integration
-   Fast update time (300ms)
-   Auto sign column

### File Types

Optimized for web development with support for:

-   JavaScript/TypeScript (.js, .ts, .jsx, .tsx)
-   JSON with schema validation
-   HTML/CSS with Emmet-like expansion
-   YAML with schema validation
-   Dockerfile syntax
-   Lua for Neovim configuration
-   Markdown with live preview

## Installation

1. Backup existing Neovim configuration:

```bash
mv ~/.config/nvim ~/.config/nvim.backup
```

2. Clone this configuration:

```bash
git clone <this-repo> ~/.config/nvim
```

3. Start Neovim - plugins will auto-install:

```bash
nvim
```

4. Check health (optional):

```
:checkhealth
```

## Troubleshooting

### Plugin Issues

-   `:Lazy` - Open plugin manager
-   `:Lazy sync` - Update all plugins
-   `:Lazy clean` - Remove unused plugins

### LSP Issues

-   `:Mason` - Open LSP installer
-   `:LspInfo` - Show LSP status
-   `:LspLog` - View LSP logs

### Performance

-   Startup time: `nvim --startuptime startup.log`
-   Plugin profiling: `:Lazy profile`

This configuration prioritizes simplicity, performance, and web development workflows while maintaining extensibility.
