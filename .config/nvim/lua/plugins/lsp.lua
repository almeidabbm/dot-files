return {
  -- LSP Configuration
  {
    "neovim/nvim-lspconfig",
    event = { "BufReadPre", "BufNewFile" },
    dependencies = {
      "williamboman/mason.nvim",
      "williamboman/mason-lspconfig.nvim",
      "b0o/schemastore.nvim",
    },
    config = function()
      -- Setup Mason first
      require("mason").setup({
        ui = {
          border = "rounded",
          icons = {
            package_installed = "✓",
            package_pending = "➜",
            package_uninstalled = "✗",
          },
        },
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
      })

      -- LSP keymaps and completion via LspAttach autocmd (Neovim 0.11 idiom)
      vim.api.nvim_create_autocmd("LspAttach", {
        callback = function(args)
          local client = vim.lsp.get_client_by_id(args.data.client_id)
          local bufnr = args.buf
          if not client then
            return
          end

          -- Enable native LSP completion
          if client:supports_method("textDocument/completion") then
            vim.lsp.completion.enable(true, client.id, bufnr, { autotrigger = true })
          end

          local function map(keys, func, desc)
            vim.keymap.set("n", keys, func, { buffer = bufnr, desc = desc })
          end

          -- Go-to commands (standard g prefix)
          map("gd", vim.lsp.buf.definition, "Go to definition")
          map("gy", vim.lsp.buf.type_definition, "Go to type definition")
          map("gi", vim.lsp.buf.implementation, "Go to implementation")
          map("gr", vim.lsp.buf.references, "Go to references")
          map("K", vim.lsp.buf.hover, "Hover documentation")

          -- Code actions (leader c prefix)
          map("<leader>cr", vim.lsp.buf.rename, "Rename symbol")
          map("<leader>ca", vim.lsp.buf.code_action, "Code action")
          map("<leader>cd", vim.diagnostic.open_float, "Line diagnostics")

          -- Diagnostic navigation
          map("[d", vim.diagnostic.goto_prev, "Previous diagnostic")
          map("]d", vim.diagnostic.goto_next, "Next diagnostic")

          -- Manual completion trigger
          vim.keymap.set("i", "<C-Space>", "<C-x><C-o>", { buffer = bufnr, desc = "Trigger completion" })
          vim.keymap.set("i", "<C-k>", vim.lsp.buf.signature_help, { buffer = bufnr, desc = "Signature help" })
        end,
      })

      -- Server configurations
      vim.lsp.config.ts_ls = {
        settings = {
          typescript = {
            inlayHints = {
              includeInlayParameterNameHints = "all",
              includeInlayParameterNameHintsWhenArgumentMatchesName = false,
              includeInlayFunctionParameterTypeHints = true,
              includeInlayVariableTypeHints = true,
            },
          },
        },
      }

      vim.lsp.config.jsonls = {
        settings = {
          json = {
            schemas = require("schemastore").json.schemas(),
            validate = { enable = true },
          },
        },
      }

      vim.lsp.config.yamlls = {
        settings = {
          yaml = {
            schemas = vim.tbl_extend("force", require("schemastore").yaml.schemas(), {
              ["file:///Users/brunoalmeida/Develop/lightdash/lightdash/packages/common/src/schemas/json/lightdash-dbt-2.0.json"] = {
                "/**/models/**/*.yml",
                "/**/models/**/*.yaml",
              },
              ["file:///Users/brunoalmeida/Develop/lightdash/lightdash/packages/common/src/schemas/json/lightdash-project-config-1.0.json"] = {
                "/**/lightdash.config.yml",
              },
            }),
          },
        },
      }

      vim.lsp.config.lua_ls = {
        settings = {
          Lua = {
            runtime = { version = "LuaJIT" },
            diagnostics = { globals = { "vim" } },
            workspace = {
              library = vim.api.nvim_get_runtime_file("", true),
              checkThirdParty = false,
            },
            telemetry = { enable = false },
          },
        },
      }

      -- Enable all servers (mason-lspconfig installs them, this activates them)
      vim.lsp.enable({
        "ts_ls",
        "eslint",
        "html",
        "cssls",
        "jsonls",
        "yamlls",
        "dockerls",
        "lua_ls",
      })

      -- Diagnostic configuration (signs defined inline, not via deprecated sign_define)
      vim.diagnostic.config({
        virtual_text = true,
        signs = {
          text = {
            [vim.diagnostic.severity.ERROR] = "✗",
            [vim.diagnostic.severity.WARN] = "⚠",
            [vim.diagnostic.severity.HINT] = "💡",
            [vim.diagnostic.severity.INFO] = "ℹ",
          },
        },
        underline = true,
        update_in_insert = false,
        severity_sort = true,
      })
    end,
  },

  -- Mason
  {
    "williamboman/mason.nvim",
    cmd = "Mason",
  },
}
