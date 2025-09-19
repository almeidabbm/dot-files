return {
  -- File tree
  {
    "nvim-tree/nvim-tree.lua",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    lazy = false,
    keys = {
      { "<leader>ft", "<cmd>NvimTreeToggle<cr>", desc = "Toggle file tree" },
      { "<leader>fe", "<cmd>NvimTreeFocus<cr>", desc = "Focus file tree" },
      { "<leader>fF", "<cmd>NvimTreeFindFile<cr>", desc = "Find file in tree" },
    },
    config = function()
      require("nvim-tree").setup({
        -- Show hidden files by default
        filters = {
          dotfiles = false,
        },
        -- Git integration
        git = {
          enable = true,
          ignore = false,
        },
        -- Disable diagnostics to avoid sign issues
        diagnostics = {
          enable = false,
        },
        -- View options
        view = {
          width = 30,
          side = "left",
        },
        -- Update focused file
        update_focused_file = {
          enable = true,
        },
        -- Actions
        actions = {
          open_file = {
            quit_on_open = false,
          },
        },
      })
    end,
  },
}