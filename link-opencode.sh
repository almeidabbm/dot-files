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

"$DOTFILES_DIR/link-agent-memory.sh"

echo ""
echo "🔗 Creating symlinks..."

mkdir -p "$HOME/.config/opencode/skills"

create_symlink "$DOTFILES_DIR/.ai/shared-instructions.md" \
               "$HOME/.config/opencode/AGENTS.md" \
               "OpenCode global rules"

for skill_dir in "$DOTFILES_DIR"/.ai/skills/*/; do
    [[ -d "$skill_dir" ]] || continue
    skill_name=$(basename "$skill_dir")
    create_symlink "$skill_dir" "$HOME/.config/opencode/skills/$skill_name" "Personal skill: $skill_name"
done

echo ""
echo "  ℹ️  Restart OpenCode to load the skills"
echo ""
echo "🎉 OpenCode setup complete!"
