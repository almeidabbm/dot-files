#!/bin/bash

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🔗 Setting up dot-files symlinks..."

# First, clean up any existing symlinks
if [[ -f "$DOTFILES_DIR/unlink.sh" ]]; then
    echo "🧹 Running cleanup first..."
    "$DOTFILES_DIR/unlink.sh"
    echo ""
else
    echo "⚠️  unlink.sh not found, proceeding with setup..."
    echo ""
fi

# Function to create symlink with better output
create_symlink() {
    local source="$1"
    local target="$2"
    local description="$3"

    # Create target directory if it doesn't exist
    mkdir -p "$(dirname "$target")"

    if ln -nfs "$source" "$target" 2>/dev/null; then
        echo "  ✅ $description: $target -> $source"
    else
        echo "  ❌ Failed to link $description: $target"
    fi
}

echo "📁 Setting up Neovim configuration..."
create_symlink "$HOME/Develop/dot-files/.config/nvim/init.lua" "$HOME/.config/nvim/init.lua" "Neovim init"
create_symlink "$HOME/Develop/dot-files/.config/nvim/lua" "$HOME/.config/nvim/lua" "Neovim Lua config"

echo ""
echo "🐚 Setting up shell configuration..."
create_symlink "$HOME/Develop/dot-files/.zshrc" "$HOME/.zshrc" "Zsh config"
create_symlink "$HOME/Develop/dot-files/.p10k.zsh" "$HOME/.p10k.zsh" "Powerlevel10k theme"

echo ""
"$DOTFILES_DIR/link-claude.sh"

echo ""
echo "🔧 Setting up tool configurations..."
create_symlink "$HOME/Develop/dot-files/.default-npm-packages" "$HOME/.default-npm-packages" "Default NPM packages"

# Platform-specific configurations
echo ""
echo "🖥️  Setting up platform-specific configs..."
if [[ `uname` == "Darwin" ]]; then
    echo "  🍎 Detected macOS"
    create_symlink "$HOME/Develop/dot-files/.fzf.mac.zsh" "$HOME/.fzf.mac.zsh" "FZF config (macOS)"
else
    echo "  🐧 Detected Linux"
    create_symlink "$HOME/Develop/dot-files/.fzf.zsh" "$HOME/.fzf.zsh" "FZF config (Linux)"
fi

echo ""
echo "🎉 Dot-files setup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Open a new terminal or run: source ~/.zshrc"
echo "  2. Launch Neovim: nvim"
echo "  3. Wait for plugins to install automatically"
echo "  4. Restart Neovim after installation completes"
