local opt = vim.opt

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

-- Completion
opt.completeopt = { "menu", "menuone", "noselect", "fuzzy" }

-- Search
opt.ignorecase = true
opt.smartcase = true

-- Auto-reload files changed externally (e.g. by Claude Code)
opt.autoread = true
vim.api.nvim_create_autocmd({ "FocusGained", "BufEnter", "CursorHold", "CursorHoldI" }, {
  command = "if mode() != 'c' | checktime | endif",
})

-- Split behavior
opt.splitbelow = true
vim.cmd("cnoreabbrev <expr> term getcmdtype() == ':' && getcmdline() ==# 'term' ? 'split \\| term' : 'term'")

