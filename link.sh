ln -nfs $HOME/Develop/dot-files/.config/nvim/init.vim $HOME/.config/nvim/init.vim
ln -nfs $HOME/Develop/dot-files/.config/nvim/coc-settings.json $HOME/.config/nvim/coc-settings.json
ln -nfs $HOME/Develop/dot-files/.zshrc $HOME/.zshrc
ln -nfs $HOME/Develop/dot-files/.p10k.zsh $HOME/.p10k.zsh
ln -nfs $HOME/Develop/dot-files/.default-npm-packages $HOME/.default-npm-packages

# When MacOS run specific config
if [[ `uname` == "Darwin" ]]; then
    ln -nfs $HOME/Develop/dot-files/.fzf.zsh $HOME/.fzf.zsh
else
    ln -nfs $HOME/Develop/dot-files/.fzf.mac.zsh $HOME/.fzf.mac.zsh
fi
