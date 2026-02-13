#!/bin/bash

echo "🧹 Cleaning up symlinks pointing to dot-files..."

# Function to remove symlink if it exists and points to dot-files
remove_symlink() {
    local target="$1"
    local description="$2"

    if [[ -L "$target" ]]; then
        local link_target=$(readlink "$target")
        if [[ "$link_target" == *"$HOME/Develop/dot-files"* ]]; then
            echo "  ❌ Removing: $target -> $link_target"
            rm "$target"
        else
            echo "  ⚠️  Skipping: $target (points to $link_target, not dot-files)"
        fi
    elif [[ -e "$target" ]]; then
        echo "  ⚠️  Skipping: $target (exists but is not a symlink)"
    else
        echo "  ✅ Already clean: $target"
    fi
}

echo ""
echo "📁 Neovim configuration:"
remove_symlink "$HOME/.config/nvim/init.vim" "Old Vim config"
remove_symlink "$HOME/.config/nvim/init.lua" "Lua config"
remove_symlink "$HOME/.config/nvim/lua" "Lua directory"
remove_symlink "$HOME/.config/nvim/coc-settings.json" "CoC settings"

echo ""
echo "🐚 Shell configuration:"
remove_symlink "$HOME/.zshrc" "Zsh config"
remove_symlink "$HOME/.p10k.zsh" "Powerlevel10k config"

echo ""
"$(cd "$(dirname "$0")" && pwd)/unlink-claude.sh"

echo ""
echo "🔧 Tool configurations:"
remove_symlink "$HOME/.default-npm-packages" "NPM packages"
remove_symlink "$HOME/.fzf.zsh" "FZF config (Linux)"
remove_symlink "$HOME/.fzf.mac.zsh" "FZF config (macOS)"

echo ""
echo "🔍 Searching for any remaining dot-files symlinks..."

# Only search in common config directories to avoid privacy prompts
search_dirs=(
    "$HOME"
    "$HOME/.config"
    "$HOME/.local"
    "$HOME/bin"
    "$HOME/.local/bin"
)

found_links=""
for dir in "${search_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        while read -r link; do
            if [[ -n "$link" && $(readlink "$link" 2>/dev/null) == *"$HOME/Develop/dot-files"* ]]; then
                found_links="$found_links$link"$'\n'
            fi
        done < <(find "$dir" -maxdepth 2 -type l 2>/dev/null)
    fi
done

if [[ -n "$found_links" ]]; then
    echo "⚠️  Found additional symlinks:"
    echo "$found_links" | while read -r link; do
        echo "  $link -> $(readlink "$link")"
    done
    echo ""
    echo "To remove these manually, run:"
    echo "$found_links" | while read -r link; do
        echo "  rm \"$link\""
    done
else
    echo "✅ No additional symlinks found"
fi

echo ""
echo "🎉 Cleanup complete! You can now run ./link.sh to create fresh symlinks."