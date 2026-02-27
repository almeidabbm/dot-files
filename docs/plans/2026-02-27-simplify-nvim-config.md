# Simplify Neovim Config Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Simplify the existing nvim config by removing unnecessary plugins, switching to Space leader, adding Harpoon/diffview/git-conflict/claudecode.nvim/catppuccin, replacing nvim-cmp with Neovim 0.11 native completion, replacing none-ls with conform.nvim, and creating a keybindings cheatsheet.

**Architecture:** Modular lazy.nvim config with `lua/config/` for core settings and `lua/plugins/` for plugin specs. We simplify by leveraging Neovim 0.11's built-in LSP completion, removing nvim-tree (use Telescope + Harpoon instead), removing alpha dashboard, and replacing none-ls with the simpler conform.nvim. We add diffview.nvim + git-conflict.nvim for merge workflows, harpoon for file navigation, claudecode.nvim for Claude Code CLI integration, and catppuccin theme.

**Tech Stack:** Neovim 0.11.4, Lua, lazy.nvim plugin manager

---

## Summary of Changes

**Plugins to REMOVE (8 plugins):**
- `alpha-nvim` (dashboard — unnecessary startup screen)
- `nvim-tree` (file tree — replaced by Telescope + Harpoon workflow)
- `nvim-cmp` + `cmp-nvim-lsp` + `cmp-buffer` + `cmp-path` + `cmp-cmdline` + `cmp_luasnip` + `LuaSnip` + `friendly-snippets` (8 packages — nvim 0.11 has native completion)
- `none-ls.nvim` + `mason-null-ls.nvim` (replaced by conform.nvim)
- `better-escape.nvim` (replace with simple keymap)
- `dracula.nvim` (replaced by catppuccin)

**Plugins to ADD (6 plugins):**
- `catppuccin/nvim` (theme)
- `harpoon` (file navigation)
- `diffview.nvim` (diff viewing + merge conflicts)
- `git-conflict.nvim` (inline merge conflict resolution)
- `conform.nvim` (formatting — simpler than none-ls)
- `claudecode.nvim` (Claude Code CLI integration)

**Net result:** ~22 plugins (down from 31). Cleaner, more documented, easier to use.

---

### Task 1: Switch Leader Key to Space

**Files:**
- Modify: `.config/nvim/init.lua:16-17`

**Step 1: Update leader key**

Change lines 16-17 in `init.lua` from:
```lua
vim.g.mapleader = ";"
vim.g.maplocalleader = ";"
```
to:
```lua
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"
```

**Step 2: Verify**

Open nvim. Press Space. which-key should show available keybindings after a short delay.

**Step 3: Commit**

```bash
git add .config/nvim/init.lua
git commit -m "refactor(nvim): switch leader key from ; to Space"
```

---

### Task 2: Replace Theme — Dracula to Catppuccin

**Files:**
- Modify: `.config/nvim/lua/plugins/ui.lua:1-10` (replace dracula block with catppuccin)
- Modify: `.config/nvim/lua/plugins/ui.lua` (lualine theme reference)
- Modify: `.config/nvim/lua/config/lazy.lua:11` (colorscheme in install config)

**Step 1: Replace the colorscheme plugin block in `ui.lua`**

Replace the dracula block (lines 1-10) with:
```lua
return {
  -- Colorscheme
  {
    "catppuccin/nvim",
    name = "catppuccin",
    lazy = false,
    priority = 1000,
    opts = {
      flavour = "mocha",
      integrations = {
        gitsigns = true,
        harpoon = true,
        indent_blankline = { enabled = true },
        mason = true,
        telescope = { enabled = true },
        treesitter = true,
        which_key = true,
      },
    },
    config = function(_, opts)
      require("catppuccin").setup(opts)
      vim.cmd.colorscheme("catppuccin")
    end,
  },
```

**Step 2: Update lualine theme**

In the lualine config section of `ui.lua`, change:
```lua
theme = "dracula",
```
to:
```lua
theme = "catppuccin",
```

Also update the lualine extensions to remove "fugitive" and "fzf" (not installed):
```lua
extensions = { "lazy", "mason" },
```

**Step 3: Update lazy.lua install colorscheme**

In `.config/nvim/lua/config/lazy.lua`, change:
```lua
colorscheme = { "dracula" },
```
to:
```lua
colorscheme = { "catppuccin" },
```

**Step 4: Verify**

Open nvim. The theme should be catppuccin mocha (dark, warm purples/blues). Lualine should match.

**Step 5: Commit**

```bash
git add .config/nvim/lua/plugins/ui.lua .config/nvim/lua/config/lazy.lua
git commit -m "feat(nvim): switch theme from dracula to catppuccin mocha"
```

---

### Task 3: Remove Dashboard, File Tree, and Better Escape

**Files:**
- Delete contents of: `.config/nvim/lua/plugins/dashboard.lua`
- Delete contents of: `.config/nvim/lua/plugins/filetree.lua`
- Modify: `.config/nvim/lua/plugins/editor.lua` (remove better-escape block, add jk/jj mapping inline)
- Modify: `.config/nvim/lua/config/options.lua` (remove netrw disable since no nvim-tree)
- Modify: `.config/nvim/lua/config/keymaps.lua` (remove file tree keymaps, add jk escape)

**Step 1: Empty the dashboard plugin file**

Replace the entire content of `.config/nvim/lua/plugins/dashboard.lua` with:
```lua
-- Dashboard removed for simplicity. Nvim opens to an empty buffer.
return {}
```

**Step 2: Empty the filetree plugin file**

Replace the entire content of `.config/nvim/lua/plugins/filetree.lua` with:
```lua
-- File tree removed. Use Telescope (<leader>ff) and Harpoon for navigation.
return {}
```

**Step 3: Remove better-escape from editor.lua**

Remove the entire better-escape block (lines 188-198) from `editor.lua`.

**Step 4: Add jk escape mapping to keymaps.lua**

Add to `.config/nvim/lua/config/keymaps.lua`:
```lua
-- Quick escape from insert mode
keymap("i", "jk", "<Esc>", { desc = "Exit insert mode" })
```

**Step 5: Remove netrw disable from options.lua**

Remove these lines from `.config/nvim/lua/config/options.lua`:
```lua
-- Disable netrw early (for nvim-tree to hijack directory opening)
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1
```

This re-enables netrw as a simple directory browser fallback (`:Ex` command).

**Step 6: Remove file tree keymaps from which-key and ui.lua**

In `ui.lua`, in the which-key spec, the `<leader>f` group description should change to just `"find"` (since it's no longer find/files with the tree):
```lua
{ "<leader>f", group = "find" },
```

**Step 7: Verify**

Open nvim. No dashboard should appear. `:Ex` should open netrw for directory browsing. `jk` in insert mode should escape to normal mode.

**Step 8: Commit**

```bash
git add .config/nvim/lua/plugins/dashboard.lua .config/nvim/lua/plugins/filetree.lua .config/nvim/lua/plugins/editor.lua .config/nvim/lua/config/keymaps.lua .config/nvim/lua/config/options.lua .config/nvim/lua/plugins/ui.lua
git commit -m "refactor(nvim): remove dashboard, file tree, and better-escape

Use Telescope + Harpoon for file navigation instead of nvim-tree.
Re-enable netrw as fallback directory browser.
Replace better-escape plugin with simple jk keymap."
```

---

### Task 4: Replace nvim-cmp with Neovim 0.11 Native Completion

Neovim 0.11 has built-in completion via `vim.lsp.completion`. This eliminates 8 plugin packages.

**Files:**
- Rewrite: `.config/nvim/lua/plugins/completion.lua`
- Modify: `.config/nvim/lua/plugins/lsp.lua` (remove cmp-nvim-lsp dependency, update capabilities)
- Modify: `.config/nvim/lua/plugins/editor.lua` (remove autopairs cmp integration)

**Step 1: Replace completion.lua with native completion setup**

Replace the entire content of `.config/nvim/lua/plugins/completion.lua` with:
```lua
-- Native Neovim 0.11 completion — no plugins needed.
-- LSP completion is enabled via vim.lsp.completion.enable() in lsp.lua.
--
-- Keybindings (built-in):
--   <C-n>     Next completion item
--   <C-p>     Previous completion item
--   <C-y>     Accept completion
--   <C-e>     Dismiss completion
--   <C-Space> Trigger completion manually (mapped in lsp.lua)
return {}
```

**Step 2: Update lsp.lua — remove cmp dependency, enable native completion**

In `.config/nvim/lua/plugins/lsp.lua`:

1. Remove `"hrsh7th/cmp-nvim-lsp"` from the dependencies list (line 9).

2. Remove the capabilities line:
```lua
local capabilities = require("cmp_nvim_lsp").default_capabilities()
```

3. In the `on_attach` function, add native completion enablement:
```lua
local on_attach = function(client, bufnr)
  -- Enable native LSP completion
  if client:supports_method("textDocument/completion") then
    vim.lsp.completion.enable(true, client.id, bufnr, { autotrigger = true })
  end

  local opts = { buffer = bufnr, remap = false }
  -- ... (keep all existing keymaps)

  -- Manual completion trigger
  vim.keymap.set("i", "<C-Space>", function()
    vim.lsp.completion.trigger()
  end, { buffer = bufnr, desc = "Trigger completion" })
end
```

4. Remove `capabilities = capabilities,` from ALL server config blocks (ts_ls, eslint, html, cssls, jsonls, yamlls, dockerls, lua_ls). The native completion doesn't need explicit capabilities.

**Step 3: Update autopairs in editor.lua**

In `.config/nvim/lua/plugins/editor.lua`, remove the cmp integration from the autopairs config. Replace the autopairs block with:
```lua
  -- Auto pairs
  {
    "windwp/nvim-autopairs",
    event = "InsertEnter",
    opts = {
      check_ts = true,
    },
  },
```

**Step 4: Verify**

Open nvim, open a TypeScript file. Start typing. Completion menu should appear automatically from LSP. `<C-n>`/`<C-p>` to navigate, `<C-y>` to confirm, `<C-Space>` to trigger manually.

**Step 5: Commit**

```bash
git add .config/nvim/lua/plugins/completion.lua .config/nvim/lua/plugins/lsp.lua .config/nvim/lua/plugins/editor.lua
git commit -m "refactor(nvim): replace nvim-cmp with neovim 0.11 native completion

Removes 8 plugin packages (nvim-cmp, cmp-nvim-lsp, cmp-buffer, cmp-path,
cmp-cmdline, LuaSnip, cmp_luasnip, friendly-snippets).
Uses vim.lsp.completion.enable() with autotrigger."
```

---

### Task 5: Replace none-ls with conform.nvim for Formatting

**Files:**
- Rewrite: `.config/nvim/lua/plugins/formatting.lua`

**Step 1: Replace formatting.lua entirely**

Replace the content of `.config/nvim/lua/plugins/formatting.lua` with:
```lua
return {
  -- Formatting with conform.nvim (simpler than none-ls)
  {
    "stevearc/conform.nvim",
    event = { "BufWritePre" },
    cmd = { "ConformInfo" },
    keys = {
      {
        "<leader>cf",
        function()
          require("conform").format({ async = true, lsp_fallback = true })
        end,
        desc = "Format buffer",
      },
    },
    opts = {
      formatters_by_ft = {
        javascript = { "prettier" },
        typescript = { "prettier" },
        javascriptreact = { "prettier" },
        typescriptreact = { "prettier" },
        vue = { "prettier" },
        css = { "prettier" },
        scss = { "prettier" },
        html = { "prettier" },
        json = { "prettier" },
        jsonc = { "prettier" },
        yaml = { "prettier" },
        markdown = { "prettier" },
        graphql = { "prettier" },
        lua = { "stylua" },
      },
      format_on_save = {
        timeout_ms = 3000,
        lsp_fallback = true,
      },
    },
  },
}
```

Note: conform.nvim finds prettier/stylua from Mason's install path automatically. No mason-null-ls bridge needed.

**Step 2: Update lsp.lua — remove ESLint format-on-save autocmd**

In `.config/nvim/lua/plugins/lsp.lua`, in the eslint config block, remove the BufWritePre autocmd that calls `EslintFixAll`. conform.nvim handles formatting now. Replace the eslint block with:
```lua
      vim.lsp.config.eslint = {
        on_attach = on_attach,
      }
```

**Step 3: Update lsp.lua — remove the manual format keymap**

In the `on_attach` function in lsp.lua, remove the `<leader>lf` format keymap (lines 60-62) since formatting is now handled by conform.nvim with `<leader>cf`.

**Step 4: Verify**

Open nvim, run `:ConformInfo` to see configured formatters. Open a JS file, save — it should auto-format with prettier.

**Step 5: Commit**

```bash
git add .config/nvim/lua/plugins/formatting.lua .config/nvim/lua/plugins/lsp.lua
git commit -m "refactor(nvim): replace none-ls with conform.nvim for formatting

Simpler configuration, no mason bridge needed.
Format on save and manual format with <leader>cf."
```

---

### Task 6: Add Harpoon for File Navigation

**Files:**
- Create: `.config/nvim/lua/plugins/navigation.lua`

**Step 1: Create navigation.lua with Harpoon 2 config**

Create `.config/nvim/lua/plugins/navigation.lua`:
```lua
return {
  -- Harpoon 2 — mark and jump to key files
  -- Mark files:    <leader>a     (add current file)
  -- Jump to marks: <leader>1-5   (jump to marked file 1-5)
  -- View marks:    <leader>h     (toggle harpoon menu)
  {
    "ThePrimeagen/harpoon",
    branch = "harpoon2",
    dependencies = { "nvim-lua/plenary.nvim" },
    keys = {
      {
        "<leader>a",
        function()
          require("harpoon"):list():add()
        end,
        desc = "Harpoon: add file",
      },
      {
        "<leader>h",
        function()
          local harpoon = require("harpoon")
          harpoon.ui:toggle_quick_menu(harpoon:list())
        end,
        desc = "Harpoon: toggle menu",
      },
      {
        "<leader>1",
        function()
          require("harpoon"):list():select(1)
        end,
        desc = "Harpoon: file 1",
      },
      {
        "<leader>2",
        function()
          require("harpoon"):list():select(2)
        end,
        desc = "Harpoon: file 2",
      },
      {
        "<leader>3",
        function()
          require("harpoon"):list():select(3)
        end,
        desc = "Harpoon: file 3",
      },
      {
        "<leader>4",
        function()
          require("harpoon"):list():select(4)
        end,
        desc = "Harpoon: file 4",
      },
      {
        "<leader>5",
        function()
          require("harpoon"):list():select(5)
        end,
        desc = "Harpoon: file 5",
      },
    },
    config = function()
      require("harpoon"):setup({})
    end,
  },
}
```

**Step 2: Verify**

Open nvim, open a file. Press `<leader>a` to mark it. Press `<leader>h` to see the Harpoon menu. Press `<leader>1` to jump to it.

**Step 3: Commit**

```bash
git add .config/nvim/lua/plugins/navigation.lua
git commit -m "feat(nvim): add harpoon 2 for file navigation

Mark files with <leader>a, jump with <leader>1-5, menu with <leader>h.
Replaces nvim-tree for working file navigation."
```

---

### Task 7: Add diffview.nvim + git-conflict.nvim

**Files:**
- Create: `.config/nvim/lua/plugins/git.lua`
- Modify: `.config/nvim/lua/plugins/ui.lua` (move gitsigns from ui.lua to git.lua)

**Step 1: Move gitsigns out of ui.lua into the new git.lua**

Remove the entire gitsigns block from `.config/nvim/lua/plugins/ui.lua` (lines 122-154).

**Step 2: Create git.lua with gitsigns + diffview + git-conflict**

Create `.config/nvim/lua/plugins/git.lua`:
```lua
return {
  -- Gitsigns — inline git change markers and hunk operations
  -- ]h / [h       Navigate between hunks
  -- <leader>gp    Preview hunk
  -- <leader>gs    Stage hunk
  -- <leader>gr    Reset hunk
  -- <leader>gS    Stage entire buffer
  -- <leader>gb    Blame current line
  {
    "lewis6991/gitsigns.nvim",
    event = { "BufReadPre", "BufNewFile" },
    opts = {
      signs = {
        add = { text = "▎" },
        change = { text = "▎" },
        delete = { text = "" },
        topdelete = { text = "" },
        changedelete = { text = "▎" },
        untracked = { text = "▎" },
      },
      on_attach = function(buffer)
        local gs = package.loaded.gitsigns

        local function map(mode, l, r, desc)
          vim.keymap.set(mode, l, r, { buffer = buffer, desc = desc })
        end

        -- Navigation
        map("n", "]h", gs.next_hunk, "Next hunk")
        map("n", "[h", gs.prev_hunk, "Prev hunk")

        -- Actions
        map({ "n", "v" }, "<leader>gs", ":Gitsigns stage_hunk<CR>", "Stage hunk")
        map({ "n", "v" }, "<leader>gr", ":Gitsigns reset_hunk<CR>", "Reset hunk")
        map("n", "<leader>gS", gs.stage_buffer, "Stage buffer")
        map("n", "<leader>gR", gs.reset_buffer, "Reset buffer")
        map("n", "<leader>gp", gs.preview_hunk, "Preview hunk")
        map("n", "<leader>gb", function()
          gs.blame_line({ full = true })
        end, "Blame line")
        map("n", "<leader>gd", gs.diffthis, "Diff this file")
      end,
    },
  },

  -- Diffview — side-by-side diff viewer for reviewing changes and merge conflicts
  -- <leader>gv    Open diff view (all changes vs index)
  -- <leader>gc    Open diff view for merge conflicts
  -- <leader>gq    Close diff view
  -- <leader>gl    File history for current file
  --
  -- Inside diffview:
  --   <Tab>       Next file
  --   <S-Tab>     Previous file
  --   [x / ]x     Previous/next conflict
  {
    "sindrets/diffview.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    cmd = { "DiffviewOpen", "DiffviewClose", "DiffviewFileHistory" },
    keys = {
      { "<leader>gv", "<cmd>DiffviewOpen<cr>", desc = "Open diff view" },
      { "<leader>gc", "<cmd>DiffviewOpen --imply-local<cr>", desc = "Open merge conflict view" },
      { "<leader>gq", "<cmd>DiffviewClose<cr>", desc = "Close diff view" },
      { "<leader>gl", "<cmd>DiffviewFileHistory %<cr>", desc = "File history (current)" },
    },
    opts = {
      enhanced_diff_hl = true,
      view = {
        merge_tool = {
          layout = "diff3_mixed",
        },
      },
    },
  },

  -- Git conflict — inline conflict resolution with keybinds
  -- co    Choose ours (current/local changes)
  -- ct    Choose theirs (incoming changes)
  -- cb    Choose both
  -- c0    Choose none
  -- ]x    Next conflict
  -- [x    Previous conflict
  {
    "akinsho/git-conflict.nvim",
    version = "*",
    event = { "BufReadPre" },
    opts = {
      default_mappings = true,    -- co, ct, cb, c0, ]x, [x
      disable_diagnostics = true, -- less noise during conflict resolution
    },
  },
}
```

**Step 3: Update which-key groups in ui.lua**

In the which-key spec in `ui.lua`, replace the git groups:
```lua
        { "<leader>g", group = "git" },
        { "<leader>gh", group = "git hunks" },
```
with:
```lua
        { "<leader>g", group = "git" },
```

(The `gh` subgroup is no longer needed since gitsigns keymaps are now flattened under `<leader>g`.)

**Step 4: Verify**

Open nvim in a git repo. Make a change. Press `<leader>gv` to open diffview — should show side-by-side diff. Press `<leader>gq` to close.

**Step 5: Commit**

```bash
git add .config/nvim/lua/plugins/git.lua .config/nvim/lua/plugins/ui.lua
git commit -m "feat(nvim): add diffview and git-conflict for diffs and merge resolution

Move gitsigns to dedicated git.lua file.
Add diffview.nvim for side-by-side diffs (<leader>gv).
Add git-conflict.nvim for inline conflict resolution (co/ct/cb)."
```

---

### Task 8: Add claudecode.nvim for Claude Code Integration

**Files:**
- Create: `.config/nvim/lua/plugins/ai.lua`

**Step 1: Create ai.lua with claudecode.nvim**

Create `.config/nvim/lua/plugins/ai.lua`:
```lua
return {
  -- Claude Code CLI integration
  -- When you run `claude` in a terminal, it auto-connects to this nvim instance.
  -- Enables: file selection, diff application, editor context sharing.
  --
  -- Usage: Open a terminal split, run `claude`, and it connects automatically.
  -- <leader>ac    Toggle Claude Code terminal
  -- <leader>as    Send visual selection to Claude
  {
    "coder/claudecode.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    keys = {
      { "<leader>ac", "<cmd>ClaudeCodeToggle<cr>", desc = "Toggle Claude Code" },
      {
        "<leader>as",
        "<cmd>ClaudeCodeSend<cr>",
        mode = "v",
        desc = "Send to Claude Code",
      },
    },
    opts = {
      terminal = {
        split_side = "right",
        split_width_percentage = 0.4,
      },
    },
  },
}
```

**Step 2: Add which-key group for AI in ui.lua**

In the which-key spec in `ui.lua`, add:
```lua
        { "<leader>a", group = "ai/harpoon" },
```

**Step 3: Verify**

Open nvim, press `<leader>ac`. A terminal split should open on the right. Type `claude` in it — it should connect to the nvim instance.

**Step 4: Commit**

```bash
git add .config/nvim/lua/plugins/ai.lua .config/nvim/lua/plugins/ui.lua
git commit -m "feat(nvim): add claudecode.nvim for Claude Code CLI integration

Toggle Claude terminal with <leader>ac.
Send visual selection with <leader>as."
```

---

### Task 9: Clean Up and Standardize Keybindings

Now that all plugins are in place, standardize the keybinding scheme across all files.

**Files:**
- Modify: `.config/nvim/lua/config/keymaps.lua` (clean up, standardize)
- Modify: `.config/nvim/lua/plugins/editor.lua` (update telescope keys to match new scheme)
- Modify: `.config/nvim/lua/plugins/lsp.lua` (standardize LSP keymaps to use `<leader>c` prefix for "code")
- Modify: `.config/nvim/lua/plugins/ui.lua` (update which-key groups)

**Step 1: Rewrite keymaps.lua with standardized bindings**

Replace `.config/nvim/lua/config/keymaps.lua` entirely:
```lua
local keymap = vim.keymap.set

-- Navigation: scroll and center
keymap("n", "<C-d>", "<C-d>zz", { desc = "Scroll down and center" })
keymap("n", "<C-u>", "<C-u>zz", { desc = "Scroll up and center" })

-- Navigation: move between windows
keymap("n", "<C-h>", "<C-w>h", { desc = "Go to left window" })
keymap("n", "<C-j>", "<C-w>j", { desc = "Go to lower window" })
keymap("n", "<C-k>", "<C-w>k", { desc = "Go to upper window" })
keymap("n", "<C-l>", "<C-w>l", { desc = "Go to right window" })

-- Navigation: resize windows with arrows
keymap("n", "<C-Up>", "<cmd>resize -2<cr>", { desc = "Decrease window height" })
keymap("n", "<C-Down>", "<cmd>resize +2<cr>", { desc = "Increase window height" })
keymap("n", "<C-Left>", "<cmd>vertical resize -2<cr>", { desc = "Decrease window width" })
keymap("n", "<C-Right>", "<cmd>vertical resize +2<cr>", { desc = "Increase window width" })

-- Editing: move lines
keymap("n", "<A-j>", "<cmd>m .+1<cr>==", { desc = "Move line down" })
keymap("n", "<A-k>", "<cmd>m .-2<cr>==", { desc = "Move line up" })
keymap("v", "<A-j>", ":m '>+1<cr>gv=gv", { desc = "Move selection down" })
keymap("v", "<A-k>", ":m '<-2<cr>gv=gv", { desc = "Move selection up" })

-- Editing: stay in visual mode after indent
keymap("v", "<", "<gv", { desc = "Indent left" })
keymap("v", ">", ">gv", { desc = "Indent right" })

-- Editing: paste without yanking in visual mode
keymap("v", "p", '"_dP', { desc = "Paste without yanking" })

-- Quick escape from insert mode
keymap("i", "jk", "<Esc>", { desc = "Exit insert mode" })

-- Clear search highlights
keymap({ "n", "i" }, "<Esc>", "<cmd>noh<cr><Esc>", { desc = "Clear search highlights" })

-- Save file
keymap({ "i", "x", "n", "s" }, "<C-s>", "<cmd>w<cr><Esc>", { desc = "Save file" })

-- Quit
keymap("n", "<leader>qq", "<cmd>qa<cr>", { desc = "Quit all" })

-- Windows
keymap("n", "<leader>ww", "<C-W>p", { desc = "Other window" })
keymap("n", "<leader>wd", "<C-W>c", { desc = "Delete window" })
keymap("n", "<leader>ws", "<C-W>s", { desc = "Split below" })
keymap("n", "<leader>wv", "<C-W>v", { desc = "Split right" })

-- Buffers
keymap("n", "<leader>bd", "<cmd>bdelete<cr>", { desc = "Delete buffer" })
keymap("n", "<S-h>", "<cmd>bprevious<cr>", { desc = "Previous buffer" })
keymap("n", "<S-l>", "<cmd>bnext<cr>", { desc = "Next buffer" })
```

Note: tabs section removed (use Harpoon + buffers instead). Window split keys standardized to `ws`/`wv` (mnemonic: **w**indow **s**plit, **w**indow **v**ertical).

**Step 2: Standardize LSP keymaps to `<leader>c` prefix**

In `.config/nvim/lua/plugins/lsp.lua`, update the `on_attach` keymaps:
```lua
    local on_attach = function(client, bufnr)
      -- Enable native LSP completion
      if client:supports_method("textDocument/completion") then
        vim.lsp.completion.enable(true, client.id, bufnr, { autotrigger = true })
      end

      local opts = { buffer = bufnr, remap = false }

      -- Go-to commands (standard g prefix)
      vim.keymap.set("n", "gd", vim.lsp.buf.definition, vim.tbl_extend("force", opts, { desc = "Go to definition" }))
      vim.keymap.set("n", "gy", vim.lsp.buf.type_definition, vim.tbl_extend("force", opts, { desc = "Go to type definition" }))
      vim.keymap.set("n", "gi", vim.lsp.buf.implementation, vim.tbl_extend("force", opts, { desc = "Go to implementation" }))
      vim.keymap.set("n", "gr", vim.lsp.buf.references, vim.tbl_extend("force", opts, { desc = "Go to references" }))
      vim.keymap.set("n", "K", vim.lsp.buf.hover, vim.tbl_extend("force", opts, { desc = "Hover documentation" }))

      -- Code actions (leader c prefix)
      vim.keymap.set("n", "<leader>cr", vim.lsp.buf.rename, vim.tbl_extend("force", opts, { desc = "Rename symbol" }))
      vim.keymap.set("n", "<leader>ca", vim.lsp.buf.code_action, vim.tbl_extend("force", opts, { desc = "Code action" }))
      vim.keymap.set("n", "<leader>cd", vim.diagnostic.open_float, vim.tbl_extend("force", opts, { desc = "Line diagnostics" }))

      -- Diagnostic navigation
      vim.keymap.set("n", "[d", vim.diagnostic.goto_prev, vim.tbl_extend("force", opts, { desc = "Previous diagnostic" }))
      vim.keymap.set("n", "]d", vim.diagnostic.goto_next, vim.tbl_extend("force", opts, { desc = "Next diagnostic" }))

      -- Manual completion trigger
      vim.keymap.set("i", "<C-Space>", function()
        vim.lsp.completion.trigger()
      end, { buffer = bufnr, desc = "Trigger completion" })
    end
```

Changes: `<leader>l*` → `<leader>c*` (mnemonic: **c**ode), `[g`/`]g` → `[d`/`]d` (standard diagnostic navigation convention).

**Step 3: Update Telescope keys in editor.lua**

In the Telescope `keys` table in `.config/nvim/lua/plugins/editor.lua`, keep find keys under `<leader>f` and move git keys to `<leader>g`:
```lua
    keys = {
      { "<leader>ff", "<cmd>Telescope find_files<cr>", desc = "Find files" },
      { "<leader>fg", "<cmd>Telescope live_grep<cr>", desc = "Live grep" },
      { "<leader>fr", "<cmd>Telescope oldfiles<cr>", desc = "Recent files" },
      { "<leader>fb", "<cmd>Telescope buffers<cr>", desc = "Buffers" },
      { "<leader>fh", "<cmd>Telescope help_tags<cr>", desc = "Help" },
      { "<leader>fd", "<cmd>Telescope diagnostics<cr>", desc = "Diagnostics" },
    },
```

(Removed `<leader>gs` and `<leader>gf` telescope git keys — the `<leader>g` group is now for gitsigns/diffview operations. Use `<leader>fg` for grep, `<leader>ff` for files which already covers git files.)

**Step 4: Update which-key groups in ui.lua**

Replace the entire `spec` section of which-key in `ui.lua`:
```lua
      spec = {
        { "<leader>a", group = "ai/harpoon" },
        { "<leader>b", group = "buffers" },
        { "<leader>c", group = "code" },
        { "<leader>f", group = "find" },
        { "<leader>g", group = "git" },
        { "<leader>q", group = "quit" },
        { "<leader>w", group = "windows" },
        { "<leader>x", group = "diagnostics" },
      },
```

**Step 5: Verify**

Open nvim, press `<leader>` and wait — which-key should show: `a` ai/harpoon, `b` buffers, `c` code, `f` find, `g` git, `q` quit, `w` windows, `x` diagnostics. Test `<leader>ff` opens file finder. Test `gd` goes to definition. Test `<leader>cr` renames.

**Step 6: Commit**

```bash
git add .config/nvim/lua/config/keymaps.lua .config/nvim/lua/plugins/lsp.lua .config/nvim/lua/plugins/editor.lua .config/nvim/lua/plugins/ui.lua
git commit -m "refactor(nvim): standardize keybindings to community conventions

Leader groups: a=ai/harpoon, b=buffers, c=code, f=find, g=git, q=quit, w=windows, x=diagnostics.
LSP keymaps use <leader>c prefix (code actions).
Diagnostic nav uses [d/]d (standard convention).
Window splits use ws/wv (mnemonic: split/vertical)."
```

---

### Task 10: Create Keybindings Cheatsheet

**Files:**
- Create: `.config/nvim/KEYBINDINGS.md`

**Step 1: Create the cheatsheet**

Create `.config/nvim/KEYBINDINGS.md`:
```markdown
# Neovim Keybindings Cheatsheet

> **Tip:** Press `<Space>` in normal mode and wait — which-key will show all available keybindings.

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
| `u` / `<C-r>` | Undo / redo |
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
| `<Esc>` or `jk` | Back to normal mode |

## Find (Space f)

| Key | Action |
|-----|--------|
| `<leader>ff` | Find files (like Cmd+P) |
| `<leader>fg` | Live grep (search in files) |
| `<leader>fr` | Recent files |
| `<leader>fb` | Open buffers |
| `<leader>fh` | Help tags |
| `<leader>fd` | Diagnostics |

## Harpoon — File Navigation (Space a/h/1-5)

| Key | Action |
|-----|--------|
| `<leader>a` | Add current file to Harpoon |
| `<leader>h` | Toggle Harpoon menu |
| `<leader>1-5` | Jump to Harpoon file 1-5 |

## Code / LSP (Space c + g-prefix)

| Key | Action |
|-----|--------|
| `gd` | Go to definition |
| `gy` | Go to type definition |
| `gi` | Go to implementation |
| `gr` | Go to references |
| `K` | Hover documentation |
| `<leader>cr` | Rename symbol |
| `<leader>ca` | Code action |
| `<leader>cd` | Line diagnostics |
| `<leader>cf` | Format buffer |
| `[d` / `]d` | Previous/next diagnostic |

## Completion (Insert Mode)

| Key | Action |
|-----|--------|
| `<C-n>` | Next completion item |
| `<C-p>` | Previous completion item |
| `<C-y>` | Accept completion |
| `<C-e>` | Dismiss completion |
| `<C-Space>` | Trigger completion manually |

## Git (Space g)

| Key | Action |
|-----|--------|
| `]h` / `[h` | Next/previous hunk |
| `<leader>gp` | Preview hunk |
| `<leader>gs` | Stage hunk |
| `<leader>gr` | Reset hunk |
| `<leader>gS` | Stage entire buffer |
| `<leader>gb` | Blame current line |
| `<leader>gd` | Diff this file |
| `<leader>gv` | Open diff view (all changes) |
| `<leader>gc` | Open merge conflict view |
| `<leader>gq` | Close diff view |
| `<leader>gl` | File history (current file) |

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
| `<leader>xx` | Toggle Trouble panel |
| `<leader>xw` | Workspace diagnostics |
| `<leader>xd` | Document diagnostics |
| `<leader>xq` | Quickfix list |
| `<leader>xl` | Location list |

## Windows (Space w)

| Key | Action |
|-----|--------|
| `<leader>ws` | Split window below |
| `<leader>wv` | Split window right |
| `<leader>wd` | Delete window |
| `<leader>ww` | Jump to other window |
| `<C-h/j/k/l>` | Navigate between windows |
| `<C-arrows>` | Resize windows |

## Buffers (Space b)

| Key | Action |
|-----|--------|
| `<leader>bd` | Delete buffer |
| `<S-h>` | Previous buffer |
| `<S-l>` | Next buffer |

## AI (Space a)

| Key | Action |
|-----|--------|
| `<leader>ac` | Toggle Claude Code terminal |
| `<leader>as` | Send visual selection to Claude (visual mode) |

## Text Editing

| Key | Action |
|-----|--------|
| `gc` | Comment/uncomment (operator) |
| `gcc` | Comment/uncomment line |
| `ys{motion}{char}` | Surround with char |
| `ds{char}` | Delete surrounding char |
| `cs{old}{new}` | Change surrounding chars |
| `<A-j>` / `<A-k>` | Move line(s) up/down |
| `<C-s>` | Save file |
| `<leader>qq` | Quit all |

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
```

**Step 2: Commit**

```bash
git add .config/nvim/KEYBINDINGS.md
git commit -m "docs(nvim): add keybindings cheatsheet"
```

---

### Task 11: Update link.sh and Symlink the Cheatsheet

**Files:**
- Modify: `.config/nvim/link.sh` — no change needed (init.lua + lua/ symlink already covers everything)

Actually, the link script already symlinks `init.lua` and `lua/` which covers all plugin files. The `KEYBINDINGS.md` file doesn't need to be symlinked (it's a reference doc in the repo). No changes needed here.

**Step 1: Verify the full config works end-to-end**

Run the following sequence:
```bash
# From the dot-files directory
./link.sh

# Open nvim — lazy.nvim should auto-install new plugins
nvim
```

Inside nvim:
1. `:Lazy` — verify all plugins install. Should see catppuccin, harpoon, diffview, git-conflict, claudecode, conform.
2. `<Space>` — which-key should show groups: a, b, c, f, g, q, w, x.
3. `<Space>ff` — Telescope file finder opens.
4. Open a TS file — completion should trigger automatically from LSP.
5. `<Space>gv` — Diffview opens.
6. `<Space>a` — Add file to harpoon. `<Space>1` to jump back.
7. `<Space>ac` — Claude Code terminal split opens.

**Step 2: Final commit (if any fixups needed)**

```bash
git add -A
git commit -m "chore(nvim): final cleanup after config simplification"
```

---

## Plugin Inventory (Final)

| # | Plugin | Purpose |
|---|--------|---------|
| 1 | lazy.nvim | Plugin manager |
| 2 | catppuccin | Theme |
| 3 | lualine.nvim | Status line |
| 4 | which-key.nvim | Keybinding discovery |
| 5 | trouble.nvim | Diagnostics panel |
| 6 | indent-blankline.nvim | Indent guides |
| 7 | nvim-treesitter | Syntax highlighting + text objects |
| 8 | nvim-treesitter-textobjects | Advanced text objects |
| 9 | telescope.nvim | Fuzzy finder |
| 10 | telescope-fzf-native | Fast sorting for telescope |
| 11 | nvim-autopairs | Auto-close brackets |
| 12 | Comment.nvim | Commenting |
| 13 | nvim-ts-context-commentstring | Context-aware comments |
| 14 | nvim-surround | Surround operations |
| 15 | nvim-lspconfig | LSP configuration |
| 16 | mason.nvim | LSP/tool installer |
| 17 | mason-lspconfig.nvim | Mason-LSP bridge |
| 18 | schemastore.nvim | JSON/YAML schemas |
| 19 | conform.nvim | Formatting |
| 20 | gitsigns.nvim | Git gutter + hunk ops |
| 21 | diffview.nvim | Side-by-side diffs |
| 22 | git-conflict.nvim | Inline conflict resolution |
| 23 | harpoon | File navigation marks |
| 24 | claudecode.nvim | Claude Code integration |
| 25 | nvim-web-devicons | File icons |
| 26 | plenary.nvim | Lua utility library |

**26 packages total** (down from 31, and many of the removed ones were heavy — nvim-cmp alone was 8 packages).
