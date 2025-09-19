local opt = vim.opt

-- Disable netrw early (for nvim-tree to hijack directory opening)
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1

-- General settings
opt.backup = false
opt.writebackup = false
opt.updatetime = 300
opt.signcolumn = "yes"
opt.clipboard = "unnamedplus"
opt.timeoutlen = 300  -- Show which-key after 300ms delay

-- UI settings
opt.number = true
opt.relativenumber = true
opt.termguicolors = true
opt.syntax = "enable"

-- Indentation
opt.tabstop = 2
opt.shiftwidth = 2
opt.expandtab = true
opt.smartindent = true

-- Search
opt.ignorecase = true
opt.smartcase = true

-- Enable true colors
if vim.fn.empty(vim.env.TMUX) == 1 then
  if vim.fn.has("nvim") == 1 then
    vim.env.NVIM_TUI_ENABLE_TRUE_COLOR = 1
  end
  if vim.fn.has("termguicolors") == 1 then
    opt.termguicolors = true
  end
end