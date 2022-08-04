call plug#begin(has('nvim') ? stdpath('data') . '/plugged' : '~/.vim/plugged')

  Plug 'neoclide/coc.nvim', {'branch': 'release'}
  Plug 'morhetz/gruvbox'
  Plug 'folke/tokyonight.nvim', { 'branch': 'main' }
  Plug 'junegunn/fzf.vim'
  Plug 'preservim/nerdtree'
  Plug 'itchyny/lightline.vim'
  Plug 'itchyny/vim-gitbranch'
  Plug 'folke/which-key.nvim'

call plug#end()

lua << EOF
  require("which-key").setup {
    -- your configuration comes here
    -- or leave it empty to use the default settings
    -- refer to the configuration section below
  }

  vim.opt.timeoutlen = 0
EOF

" Use ctrl + space for autocompletion suggestions
inoremap <silent><expr> <c-space> coc#refresh()

" Set colorscheme
autocmd vimenter * ++nested colorscheme gruvbox
set background=dark

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
