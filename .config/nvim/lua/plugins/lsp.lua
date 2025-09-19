return {
  -- LSP Configuration
  {
    "neovim/nvim-lspconfig",
    event = { "BufReadPre", "BufNewFile" },
    dependencies = {
      "williamboman/mason.nvim",
      "williamboman/mason-lspconfig.nvim",
      "hrsh7th/cmp-nvim-lsp",
    },
    config = function()
      -- Setup Mason first
      require("mason").setup({
        ui = {
          border = "rounded",
          icons = {
            package_installed = "✓",
            package_pending = "➜",
            package_uninstalled = "✗"
          }
        }
      })

      require("mason-lspconfig").setup({
        ensure_installed = {
          "ts_ls",
          "eslint",
          "html",
          "cssls",
          "jsonls",
          "yamlls",
          "dockerls",
          "lua_ls",
        },
        automatic_installation = true,
        handlers = {
          function(server_name)
            if vim.lsp.config[server_name] then
              vim.lsp.enable(server_name)
            end
          end,
        },
      })

      local capabilities = require("cmp_nvim_lsp").default_capabilities()

      -- LSP keymaps
      local on_attach = function(client, bufnr)
        local opts = { buffer = bufnr, remap = false }

        vim.keymap.set("n", "gd", vim.lsp.buf.definition, opts)
        vim.keymap.set("n", "gy", vim.lsp.buf.type_definition, opts)
        vim.keymap.set("n", "gi", vim.lsp.buf.implementation, opts)
        vim.keymap.set("n", "gr", vim.lsp.buf.references, opts)
        vim.keymap.set("n", "K", vim.lsp.buf.hover, opts)
        vim.keymap.set("n", "<leader>lr", vim.lsp.buf.rename, opts)
        vim.keymap.set("n", "<leader>la", vim.lsp.buf.code_action, opts)
        vim.keymap.set("n", "[g", vim.diagnostic.goto_prev, opts)
        vim.keymap.set("n", "]g", vim.diagnostic.goto_next, opts)
        vim.keymap.set("n", "<leader>lf", function()
          vim.lsp.buf.format({ async = true })
        end, opts)
        vim.keymap.set("n", "<leader>ld", vim.diagnostic.open_float, opts)
      end

      -- TypeScript/JavaScript
      vim.lsp.config.ts_ls = {
        capabilities = capabilities,
        on_attach = on_attach,
        settings = {
          typescript = {
            inlayHints = {
              includeInlayParameterNameHints = 'all',
              includeInlayParameterNameHintsWhenArgumentMatchesName = false,
              includeInlayFunctionParameterTypeHints = true,
              includeInlayVariableTypeHints = true,
            },
          },
        },
      }

      -- ESLint
      vim.lsp.config.eslint = {
        capabilities = capabilities,
        on_attach = function(client, bufnr)
          on_attach(client, bufnr)
          -- Enable formatting through ESLint
          vim.api.nvim_create_autocmd("BufWritePre", {
            buffer = bufnr,
            command = "EslintFixAll",
          })
        end,
      }

      -- HTML
      vim.lsp.config.html = {
        capabilities = capabilities,
        on_attach = on_attach,
      }

      -- CSS
      vim.lsp.config.cssls = {
        capabilities = capabilities,
        on_attach = on_attach,
      }

      -- JSON
      vim.lsp.config.jsonls = {
        capabilities = capabilities,
        on_attach = on_attach,
        settings = {
          json = {
            schemas = require('schemastore').json.schemas(),
            validate = { enable = true },
          },
        },
      }

      -- YAML
      vim.lsp.config.yamlls = {
        capabilities = capabilities,
        on_attach = on_attach,
        settings = {
          yaml = {
            schemas = require('schemastore').yaml.schemas(),
          },
        },
      }

      -- Docker
      vim.lsp.config.dockerls = {
        capabilities = capabilities,
        on_attach = on_attach,
      }

      -- Lua
      vim.lsp.config.lua_ls = {
        capabilities = capabilities,
        on_attach = on_attach,
        settings = {
          Lua = {
            runtime = {
              version = "LuaJIT",
            },
            diagnostics = {
              globals = { "vim" },
            },
            workspace = {
              library = vim.api.nvim_get_runtime_file("", true),
              checkThirdParty = false,
            },
            telemetry = {
              enable = false,
            },
          },
        },
      }

      -- Diagnostic configuration
      vim.diagnostic.config({
        virtual_text = true,
        signs = true,
        underline = true,
        update_in_insert = false,
        severity_sort = true,
      })

      -- Diagnostic signs - define early to avoid nvim-tree errors
      local signs = { Error = "✗", Warn = "⚠", Hint = "💡", Info = "ℹ" }
      for type, icon in pairs(signs) do
        local hl = "DiagnosticSign" .. type
        vim.fn.sign_define(hl, { text = icon, texthl = hl, numhl = "" })
      end
    end,
  },

  -- Mason
  {
    "williamboman/mason.nvim",
    cmd = "Mason",
  },

  -- Schema store for JSON/YAML
  {
    "b0o/schemastore.nvim",
    lazy = true,
  },
}