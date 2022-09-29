call plug#begin(has('nvim') ? stdpath('data') . '/plugged' : '~/.vim/plugged')

  Plug 'neoclide/coc.nvim', {'branch': 'release'}
  Plug 'junegunn/fzf.vim'
  Plug 'preservim/nerdtree'
  Plug 'itchyny/lightline.vim'
  Plug 'itchyny/vim-gitbranch'
  Plug 'folke/which-key.nvim'
  Plug 'dracula/vim', { 'as': 'dracula' }
  Plug 'nvim-treesitter/nvim-treesitter', {'do': ':TSUpdate'}

  let g:coc_global_extensions = ['coc-tslint-plugin', 'coc-tsserver', 'coc-emmet', 'coc-css', 'coc-html', 'coc-json', 'coc-prettier']

call plug#end()

lua << EOF
  require("which-key").setup {
    -- your configuration comes here
    -- or leave it empty to use the default settings
    -- refer to the configuration section below
  }

  vim.opt.timeoutlen = 0

  -- TreeSitter

  require'nvim-treesitter.configs'.setup {
    -- A list of parser names, or "all"
    ensure_installed = { "lua", "javascript", "typescript", "json", "yaml", "vim", "ruby", "python", "go", "html", "css" },

    -- Install parsers synchronously (only applied to `ensure_installed`)
    sync_install = false,

    -- Automatically install missing parsers when entering buffer
    auto_install = true,

    -- List of parsers to ignore installing (for "all")
    -- ignore_install = { "javascript" },

    ---- If you need to change the installation directory of the parsers (see -> Advanced Setup)
    -- parser_install_dir = "/some/path/to/store/parsers", -- Remember to run vim.opt.runtimepath:append("/some/path/to/store/parsers")!

    highlight = {
      -- `false` will disable the whole extension
      enable = true,

      -- NOTE: these are the names of the parsers and not the filetype. (for example if you want to
      -- disable highlighting for the `tex` filetype, you need to include `latex` in this list as this is
      -- the name of the parser)
      -- list of language that will be disabled
      -- disable = { "c", "rust" },

      -- Setting this to true will run `:h syntax` and tree-sitter at the same time.
      -- Set this to `true` if you depend on 'syntax' being enabled (like for indentation).
      -- Using this option may slow down your editor, and you may see some duplicate highlights.
      -- Instead of true it can also be a list of languages
      additional_vim_regex_highlighting = false,
    },
  }

  -- CoC

  -- Some servers have issues with backup files, see #649.
  vim.opt.backup = false
  vim.opt.writebackup = false

  -- Having longer updatetime (default is 4000 ms = 4 s) leads to noticeable
  -- delays and poor user experience.
  vim.opt.updatetime = 300

  -- Always show the signcolumn, otherwise it would shift the text each time
  -- diagnostics appear/become resolved.
  vim.opt.signcolumn = "yes"

  local keyset = vim.keymap.set
  -- Auto complete
  function _G.check_back_space()
      local col = vim.fn.col('.') - 1
      return col == 0 or vim.fn.getline('.'):sub(col, col):match('%s')
  end

  -- Use tab for trigger completion with characters ahead and navigate.
  -- NOTE: There's always complete item selected by default, you may want to enable
  -- no select by `"suggest.noselect": true` in your configuration file.
  -- NOTE: Use command ':verbose imap <tab>' to make sure tab is not mapped by
  -- other plugin before putting this into your config.
  local opts = {silent = true, noremap = true, expr = true}
  keyset("i", "<TAB>", 'coc#pum#visible() ? coc#pum#next(1) : v:lua.check_back_space() ? "<TAB>" : coc#refresh()', opts)
  keyset("i", "<S-TAB>", [[coc#pum#visible() ? coc#pum#prev(1) : "\<C-h>"]], opts)

  -- Make <CR> to accept selected completion item or notify coc.nvim to format
  -- <C-g>u breaks current undo, please make your own choice.
  keyset("i", "<cr>", [[coc#pum#visible() ? coc#pum#confirm() : "\<C-g>u\<CR>\<c-r>=coc#on_enter()\<CR>"]], opts)

  -- Use <c-j> to trigger snippets
  keyset("i", "<c-j>", "<Plug>(coc-snippets-expand-jump)")
  -- Use <c-space> to trigger completion.
  keyset("i", "<c-space>", "coc#refresh()", {silent = true, expr = true})

  -- Use `[g` and `]g` to navigate diagnostics
  -- Use `:CocDiagnostics` to get all diagnostics of current buffer in location list.
  keyset("n", "[g", "<Plug>(coc-diagnostic-prev)", {silent = true})
  keyset("n", "]g", "<Plug>(coc-diagnostic-next)", {silent = true})

  -- GoTo code navigation.
  keyset("n", "gd", "<Plug>(coc-definition)", {silent = true})
  keyset("n", "gy", "<Plug>(coc-type-definition)", {silent = true})
  keyset("n", "gi", "<Plug>(coc-implementation)", {silent = true})
  keyset("n", "gr", "<Plug>(coc-references)", {silent = true})


  -- Use K to show documentation in preview window.
  function _G.show_docs()
      local cw = vim.fn.expand('<cword>')
      if vim.fn.index({'vim', 'help'}, vim.bo.filetype) >= 0 then
          vim.api.nvim_command('h ' .. cw)
      elseif vim.api.nvim_eval('coc#rpc#ready()') then
          vim.fn.CocActionAsync('doHover')
      else
          vim.api.nvim_command('!' .. vim.o.keywordprg .. ' ' .. cw)
      end
  end
  keyset("n", "K", '<CMD>lua _G.show_docs()<CR>', {silent = true})


  -- Highlight the symbol and its references when holding the cursor.
  vim.api.nvim_create_augroup("CocGroup", {})
  vim.api.nvim_create_autocmd("CursorHold", {
      group = "CocGroup",
      command = "silent call CocActionAsync('highlight')",
      desc = "Highlight symbol under cursor on CursorHold"
  })


  -- Formatting selected code.
  keyset("x", "<leader>f", "<Plug>(coc-format-selected)", {silent = true})
  keyset("n", "<leader>f", "<Plug>(coc-format-selected)", {silent = true})


  -- Setup formatexpr specified filetype(s).
  vim.api.nvim_create_autocmd("FileType", {
      group = "CocGroup",
      pattern = "typescript,json",
      command = "setl formatexpr=CocAction('formatSelected')",
      desc = "Setup formatexpr specified filetype(s)."
  })

  -- Update signature help on jump placeholder.
  vim.api.nvim_create_autocmd("User", {
      group = "CocGroup",
      pattern = "CocJumpPlaceholder",
      command = "call CocActionAsync('showSignatureHelp')",
      desc = "Update signature help on jump placeholder"
  })


  -- Applying codeAction to the selected region.
  -- Example: `<leader>aap` for current paragraph
  local opts = {silent = true, nowait = true}
  keyset("x", "<leader>a", "<Plug>(coc-codeaction-selected)", opts)
  keyset("n", "<leader>a", "<Plug>(coc-codeaction-selected)", opts)

  -- Remap keys for applying codeAction to the current buffer.
  keyset("n", "<leader>ac", "<Plug>(coc-codeaction)", opts)


  -- Apply AutoFix to problem on the current line.
  keyset("n", "<leader>qf", "<Plug>(coc-fix-current)", opts)


  -- Run the Code Lens action on the current line.
  keyset("n", "<leader>cl", "<Plug>(coc-codelens-action)", opts)


  -- Map function and class text objects
  -- NOTE: Requires 'textDocument.documentSymbol' support from the language server.
  keyset("x", "if", "<Plug>(coc-funcobj-i)", opts)
  keyset("o", "if", "<Plug>(coc-funcobj-i)", opts)
  keyset("x", "af", "<Plug>(coc-funcobj-a)", opts)
  keyset("o", "af", "<Plug>(coc-funcobj-a)", opts)
  keyset("x", "ic", "<Plug>(coc-classobj-i)", opts)
  keyset("o", "ic", "<Plug>(coc-classobj-i)", opts)
  keyset("x", "ac", "<Plug>(coc-classobj-a)", opts)
  keyset("o", "ac", "<Plug>(coc-classobj-a)", opts)


  -- Remap <C-f> and <C-b> for scroll float windows/popups.
  ---@diagnostic disable-next-line: redefined-local
  local opts = {silent = true, nowait = true, expr = true}
  keyset("n", "<C-f>", 'coc#float#has_scroll() ? coc#float#scroll(1) : "<C-f>"', opts)
  keyset("n", "<C-b>", 'coc#float#has_scroll() ? coc#float#scroll(0) : "<C-b>"', opts)
  keyset("i", "<C-f>",
         'coc#float#has_scroll() ? "<c-r>=coc#float#scroll(1)<cr>" : "<Right>"', opts)
  keyset("i", "<C-b>",
         'coc#float#has_scroll() ? "<c-r>=coc#float#scroll(0)<cr>" : "<Left>"', opts)
  keyset("v", "<C-f>", 'coc#float#has_scroll() ? coc#float#scroll(1) : "<C-f>"', opts)
  keyset("v", "<C-b>", 'coc#float#has_scroll() ? coc#float#scroll(0) : "<C-b>"', opts)


  -- Use CTRL-S for selections ranges.
  -- Requires 'textDocument/selectionRange' support of language server.
  keyset("n", "<C-s>", "<Plug>(coc-range-select)", {silent = true})
  keyset("x", "<C-s>", "<Plug>(coc-range-select)", {silent = true})


  -- Add `:Format` command to format current buffer.
  vim.api.nvim_create_user_command("Format", "call CocAction('format')", {})

  -- " Add `:Fold` command to fold current buffer.
  vim.api.nvim_create_user_command("Fold", "call CocAction('fold', <f-args>)", {nargs = '?'})

  -- Add `:OR` command for organize imports of the current buffer.
  vim.api.nvim_create_user_command("OR", "call CocActionAsync('runCommand', 'editor.action.organizeImport')", {})

  -- Add (Neo)Vim's native statusline support.
  -- NOTE: Please see `:h coc-status` for integrations with external plugins that
  -- provide custom statusline: lightline.vim, vim-airline.
  vim.opt.statusline:prepend("%{coc#status()}%{get(b:,'coc_current_function','')}")

  -- Mappings for CoCList
  -- code actions and coc stuff
  ---@diagnostic disable-next-line: redefined-local
  local opts = {silent = true, nowait = true}
  -- Show all diagnostics.
  keyset("n", "<space>a", ":<C-u>CocList diagnostics<cr>", opts)
  -- Manage extensions.
  keyset("n", "<space>e", ":<C-u>CocList extensions<cr>", opts)
  -- Show commands.
  keyset("n", "<space>c", ":<C-u>CocList commands<cr>", opts)
  -- Find symbol of current document.
  keyset("n", "<space>o", ":<C-u>CocList outline<cr>", opts)
  -- Search workspace symbols.
  keyset("n", "<space>s", ":<C-u>CocList -I symbols<cr>", opts)
  -- Do default action for next item.
  keyset("n", "<space>j", ":<C-u>CocNext<cr>", opts)
  -- Do default action for previous item.
  keyset("n", "<space>k", ":<C-u>CocPrev<cr>", opts)
  -- Resume latest coc list.
  keyset("n", "<space>p", ":<C-u>CocListResume<cr>", opts)
EOF

syntax enable
colorscheme dracula

"Use 24-bit (true-color) mode in Vim/Neovim when outside tmux.
"If you're using tmux version 2.2 or later, you can remove the outermost $TMUX check and use tmux's 24-bit color support
"(see < http://sunaku.github.io/tmux-24bit-color.html#usage > for more information.)
if (empty($TMUX))
  if (has("nvim"))
    "For Neovim 0.1.3 and 0.1.4 < https://github.com/neovim/neovim/pull/2198 >
    let $NVIM_TUI_ENABLE_TRUE_COLOR=1
  endif
  "For Neovim > 0.1.5 and Vim > patch 7.4.1799 < https://github.com/vim/vim/commit/61be73bb0f965a895bfb064ea3e55476ac175162 >
  "Based on Vim patch 7.4.1770 (`guicolors` option) < https://github.com/vim/vim/commit/8a633e3427b47286869aa4b96f2bfc1fe65b25cd >
  " < https://github.com/neovim/neovim/wiki/Following-HEAD#20160511 >
  if (has("termguicolors"))
    set termguicolors
  endif
endif

" lightline
let g:lightline = {
  \ 'active': {
  \   'left': [ [ 'mode', 'paste' ],
  \             [ 'gitbranch', 'readonly', 'filename', 'modified' ] ]
  \ },
  \ 'component_function': {
  \   'gitbranch': 'gitbranch#name'
  \ },
\ }

set tabstop=2 shiftwidth=2 expandtab smartindent


let mapleader=";"
map <leader><C-t> :FZF<CR>
map <leader>t :NERDTreeToggle<CR>

" turn hybrid line numbers on
:set number relativenumber

" NERDTree show hidden files by default
let NERDTreeShowHidden=1
