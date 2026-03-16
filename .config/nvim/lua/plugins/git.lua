return {
  -- Gitsigns — inline git change markers, blame, and hunk operations
  -- Current line blame shown as virtual text (auto, GitLens-style)
  -- ]h / [h       Navigate between hunks
  -- <leader>gp    Preview hunk (floating popup)
  -- <leader>gs    Stage hunk
  -- <leader>gr    Reset hunk
  -- <leader>gS    Stage entire buffer
  -- <leader>gb    Blame line (full details)
  -- Use <leader>gv / <leader>gq for full diff view
  {
    "lewis6991/gitsigns.nvim",
    event = { "BufReadPre", "BufNewFile" },
    opts = {
      current_line_blame = true,
      current_line_blame_opts = { delay = 300 },
      current_line_blame_formatter = "<author>, <author_time:%R> · <summary>",
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

  -- Git graph — visual commit/branch graph
  -- <leader>gg    Open git graph
  -- <leader>gG    Open git graph for current branch only
  {
    "isakbm/gitgraph.nvim",
    dependencies = { "sindrets/diffview.nvim" },
    opts = {
      symbols = {
        merge_commit = "M",
        commit = "●",
      },
      format = {
        timestamp = "%R",
        fields = { "hash", "timestamp", "author", "branch_name", "tag" },
      },
      hooks = {
        on_select_commit = function(commit)
          vim.notify("DiffviewOpen " .. commit.hash .. "^!")
          vim.cmd(":DiffviewOpen " .. commit.hash .. "^!")
        end,
        on_select_range_commit = function(from, to)
          vim.notify("DiffviewOpen " .. from.hash .. "~1.." .. to.hash)
          vim.cmd(":DiffviewOpen " .. from.hash .. "~1.." .. to.hash)
        end,
      },
    },
    keys = {
      {
        "<leader>gg",
        function()
          require("gitgraph").draw({}, { all = true, max_count = 5000 })
        end,
        desc = "Git graph",
      },
      {
        "<leader>gG",
        function()
          require("gitgraph").draw({}, { all = false, max_count = 500 })
        end,
        desc = "Git graph (current branch)",
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
