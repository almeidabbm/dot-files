local keymap = vim.keymap.set

-- Navigation: scroll and center
keymap("n", "<C-d>", "<C-d>zz", { desc = "Scroll down and center" })
keymap("n", "<C-u>", "<C-u>zz", { desc = "Scroll up and center" })

-- Navigation: move between windows
keymap({ "n", "t" }, "<C-h>", "<C-\\><C-n><C-w>h", { desc = "Go to left window" })
keymap({ "n", "t" }, "<C-j>", "<C-\\><C-n><C-w>j", { desc = "Go to lower window" })
keymap({ "n", "t" }, "<C-k>", "<C-\\><C-n><C-w>k", { desc = "Go to upper window" })
keymap({ "n", "t" }, "<C-l>", "<C-\\><C-n><C-w>l", { desc = "Go to right window" })

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
