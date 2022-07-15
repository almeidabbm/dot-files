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

" Example config in VimScript
let g:tokyonight_style = "night"
let g:tokyonight_italic_functions = 1
let g:tokyonight_sidebars = [ "qf", "vista_kind", "terminal", "packer" ]

" Change the "hint" color to the "orange" color, and make the "error" color bright red
let g:tokyonight_colors = {
  \ 'hint': 'orange',
  \ 'error': '#ff0000'
\ }

" Load the colorscheme
colorscheme tokyonight
syntax on

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
