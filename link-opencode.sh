#!/bin/bash

# Standalone script to symlink only OpenCode configuration.
# Can be run independently without affecting other dotfiles.

DOTFILES_DIR="$HOME/Develop/dot-files"

create_symlink() {
    local source="$1"
    local target="$2"
    local description="$3"

    mkdir -p "$(dirname "$target")"

    if ln -nfs "$source" "$target" 2>/dev/null; then
        echo "  ✅ $description: $target -> $source"
    else
        echo "  ❌ Failed to link $description: $target"
    fi
}

echo "⚡ Setting up OpenCode configuration..."

if [ -d "$HOME/.config/opencode/superpowers" ]; then
    echo "  ℹ️  Updating existing superpowers..."
    cd "$HOME/.config/opencode/superpowers" && git pull
else
    echo "  📥 Cloning superpowers..."
    git clone https://github.com/obra/superpowers.git "$HOME/.config/opencode/superpowers"
fi

echo ""
echo "🔗 Creating symlinks..."

mkdir -p "$HOME/.config/opencode/plugins"
mkdir -p "$HOME/.config/opencode/skills"

rm -f "$HOME/.config/opencode/plugins/superpowers.js"
rm -rf "$HOME/.config/opencode/skills/superpowers"

create_symlink "$HOME/.config/opencode/superpowers/.opencode/plugins/superpowers.js" \
               "$HOME/.config/opencode/plugins/superpowers.js" \
               "Superpowers plugin"

create_symlink "$HOME/.config/opencode/superpowers/skills" \
               "$HOME/.config/opencode/skills/superpowers" \
               "Superpowers skills"

echo ""
echo "  ℹ️  Restart OpenCode to load the plugin and skills"
echo ""
echo "🎉 OpenCode setup complete!"
