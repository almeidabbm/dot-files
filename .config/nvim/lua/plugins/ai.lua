return {
  -- Claude Code CLI integration
  -- Auto-connects when you run `claude` in a terminal.
  -- Enables: file selection, diff application, editor context sharing.
  --
  -- <leader>ac    Toggle Claude Code terminal
  -- <leader>af    Focus Claude terminal
  -- <leader>as    Send visual selection to Claude
  -- <leader>ab    Add current buffer to Claude context
  -- <leader>aa    Accept diff from Claude
  -- <leader>ad    Deny diff from Claude
  {
    "coder/claudecode.nvim",
    config = true,
    keys = {
      { "<leader>ac", "<cmd>ClaudeCode<cr>", desc = "Toggle Claude Code" },
      { "<leader>af", "<cmd>ClaudeCodeFocus<cr>", desc = "Focus Claude" },
      { "<leader>as", "<cmd>ClaudeCodeSend<cr>", mode = "v", desc = "Send to Claude" },
      { "<leader>ab", "<cmd>ClaudeCodeAdd %<cr>", desc = "Add buffer to Claude" },
      { "<leader>aa", "<cmd>ClaudeCodeDiffAccept<cr>", desc = "Accept diff" },
      { "<leader>ad", "<cmd>ClaudeCodeDiffDeny<cr>", desc = "Deny diff" },
    },
    opts = {
      terminal = {
        split_side = "right",
        split_width_percentage = 0.4,
        provider = "native",
      },
      diff_opts = {
        open_in_new_tab = true,
        hide_terminal_in_new_tab = true,
      },
    },
  },
  {
    "nickjvandyke/opencode.nvim",
    version = "*",
    config = function()
      vim.g.opencode_opts = {}
      vim.o.autoread = true
    end,
    keys = {
      { "<leader>ao", function() require("opencode").toggle() end, desc = "Toggle OpenCode" },
    },
  },
}
