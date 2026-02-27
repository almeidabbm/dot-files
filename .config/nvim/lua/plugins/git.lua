return {
  -- Gitsigns — inline git change markers and hunk operations
  -- ]h / [h       Navigate between hunks
  -- <leader>gp    Preview hunk (floating popup)
  -- <leader>gs    Stage hunk
  -- <leader>gr    Reset hunk
  -- <leader>gS    Stage entire buffer
  -- <leader>gb    Blame current line
  -- Use <leader>gv / <leader>gq for full diff view
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
      default_mappings = true,
      disable_diagnostics = true,
    },
  },
}
