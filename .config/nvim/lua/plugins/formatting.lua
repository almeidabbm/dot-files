return {
  -- Formatting and Linting
  {
    "nvimtools/none-ls.nvim",
    event = { "BufReadPre", "BufNewFile" },
    dependencies = {
      "mason.nvim",
      "jay-babu/mason-null-ls.nvim",
    },
    config = function()
      local null_ls = require("null-ls")
      local formatting = null_ls.builtins.formatting
      local diagnostics = null_ls.builtins.diagnostics

      -- Setup mason-null-ls
      require("mason-null-ls").setup({
        ensure_installed = {
          "prettier",
          "stylua",
          "black",
          "gofmt",
          "rustfmt",
          "rubocop",
        },
        automatic_installation = true,
        handlers = {},
      })

      null_ls.setup({
        sources = {
          -- Formatting
          formatting.prettier.with({
            filetypes = {
              "javascript",
              "typescript",
              "javascriptreact",
              "typescriptreact",
              "vue",
              "css",
              "scss",
              "less",
              "html",
              "json",
              "jsonc",
              "yaml",
              "markdown",
              "markdown.mdx",
              "graphql",
              "handlebars",
            },
          }),
          formatting.stylua,
          formatting.black,
          formatting.gofmt,
          formatting.rustfmt,
          formatting.rubocop,

          -- Diagnostics (if needed beyond LSP)
          -- diagnostics.eslint_d,
        },
        on_attach = function(client, bufnr)
          if client.supports_method("textDocument/formatting") then
            -- Format on save
            vim.api.nvim_create_autocmd("BufWritePre", {
              buffer = bufnr,
              callback = function()
                vim.lsp.buf.format({
                  bufnr = bufnr,
                  filter = function(c)
                    return c.name == "null-ls"
                  end,
                })
              end,
            })
          end
        end,
      })
    end,
  },
}