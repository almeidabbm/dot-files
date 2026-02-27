# Neovim Keybindings Cheatsheet

> **Tip:** Press `Space` in normal mode and wait — which-key will show all available keybindings.

## Leader Key: `Space`

## Essential Vim Motions (built-in)

| Key | Action |
|-----|--------|
| `h/j/k/l` | Move left/down/up/right |
| `w/b` | Next/previous word |
| `e` | End of word |
| `0/$` | Start/end of line |
| `gg/G` | Top/bottom of file |
| `%` | Jump to matching bracket |
| `f{char}` | Jump to char on line |
| `ci"` | Change inside quotes |
| `da{` | Delete around braces |
| `yiw` | Yank (copy) inner word |
| `p/P` | Paste after/before |
| `u` / `Ctrl+r` | Undo / redo |
| `.` | Repeat last action |
| `/pattern` | Search forward |
| `n/N` | Next/previous search result |

## Mode Switching

| Key | Action |
|-----|--------|
| `i` | Insert before cursor |
| `a` | Insert after cursor |
| `o/O` | New line below/above |
| `v` | Visual mode |
| `V` | Visual line mode |
| `Esc` or `jk` | Back to normal mode |

## Find (Space f)

| Key | Action |
|-----|--------|
| `Space ff` | Find files (like Cmd+P) |
| `Space fg` | Live grep (search in files) |
| `Space fr` | Recent files |
| `Space fb` | Open buffers |
| `Space fh` | Help tags |
| `Space fd` | Diagnostics |

## Harpoon — File Navigation (Space h / Space 1-5)

| Key | Action |
|-----|--------|
| `Space ha` | Add current file to Harpoon |
| `Space hh` | Toggle Harpoon menu |
| `Space 1-5` | Jump to Harpoon file 1-5 |

## Code / LSP (Space c + g-prefix)

| Key | Action |
|-----|--------|
| `gd` | Go to definition |
| `gy` | Go to type definition |
| `gi` | Go to implementation |
| `gr` | Go to references |
| `K` | Hover documentation |
| `Space cr` | Rename symbol |
| `Space ca` | Code action |
| `Space cd` | Line diagnostics |
| `Space cf` | Format buffer |
| `[d` / `]d` | Previous/next diagnostic |

## Completion (Insert Mode)

| Key | Action |
|-----|--------|
| `Ctrl+n` | Next completion item |
| `Ctrl+p` | Previous completion item |
| `Ctrl+y` | Accept completion |
| `Ctrl+e` | Dismiss completion |
| `Ctrl+Space` | Trigger completion manually |

## Git (Space g)

| Key | Action |
|-----|--------|
| `]h` / `[h` | Next/previous hunk |
| `Space gp` | Preview hunk |
| `Space gs` | Stage hunk |
| `Space gr` | Reset hunk |
| `Space gS` | Stage entire buffer |
| `Space gR` | Reset entire buffer |
| `Space gb` | Blame current line |
| `Space gv` | Open diff view (all changes) |
| `Space gc` | Open merge conflict view |
| `Space gq` | Close diff view |
| `Space gl` | File history (current file) |

## Merge Conflict Resolution (git-conflict)

| Key | Action |
|-----|--------|
| `co` | Choose ours (local changes) |
| `ct` | Choose theirs (incoming changes) |
| `cb` | Choose both |
| `c0` | Choose none |
| `]x` / `[x` | Next/previous conflict |

## Diagnostics / Trouble (Space x)

| Key | Action |
|-----|--------|
| `Space xx` | Toggle Trouble panel |
| `Space xw` | Workspace diagnostics |
| `Space xd` | Document diagnostics |
| `Space xq` | Quickfix list |
| `Space xl` | Location list |

## Windows (Space w)

| Key | Action |
|-----|--------|
| `Space ws` | Split window below |
| `Space wv` | Split window right |
| `Space wd` | Delete window |
| `Space ww` | Jump to other window |
| `Ctrl+h/j/k/l` | Navigate between windows |
| `Ctrl+arrows` | Resize windows |

## Buffers (Space b)

| Key | Action |
|-----|--------|
| `Space bd` | Delete buffer |
| `Shift+h` | Previous buffer |
| `Shift+l` | Next buffer |

## AI — Claude Code (Space a)

| Key | Action |
|-----|--------|
| `Space ac` | Toggle Claude Code terminal |
| `Space af` | Focus Claude terminal (smart toggle) |
| `Space as` | Send visual selection to Claude (visual mode) |
| `Space ab` | Add current buffer to Claude's context |
| `Space aa` | Accept diff proposed by Claude |
| `Space ad` | Deny diff proposed by Claude |

## Text Editing

| Key | Action |
|-----|--------|
| `gc` | Comment/uncomment (operator) |
| `gcc` | Comment/uncomment line |
| `ys{motion}{char}` | Surround with char |
| `ds{char}` | Delete surrounding char |
| `cs{old}{new}` | Change surrounding chars |
| `Alt+j` / `Alt+k` | Move line(s) up/down |
| `Ctrl+s` | Save file |
| `Space qq` | Quit all |

## Treesitter Text Objects

| Key | Action |
|-----|--------|
| `if` / `af` | Inner/outer function |
| `ic` / `ac` | Inner/outer class |
| `ia` / `aa` | Inner/outer parameter |
| `]m` / `[m` | Next/previous function |
| `]]` / `[[` | Next/previous class |

## Useful Commands

| Command | Action |
|---------|--------|
| `:Mason` | Open Mason (LSP/tool installer) |
| `:Lazy` | Open plugin manager |
| `:ConformInfo` | Show configured formatters |
| `:checkhealth` | Diagnose nvim setup issues |
| `:Ex` | Open file explorer (netrw) |
