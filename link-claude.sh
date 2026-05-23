#!/bin/bash

# Standalone script to symlink only Claude Code configuration.
# Can be run independently without affecting other dotfiles.

DOTFILES_DIR="$HOME/Develop/dot-files"

# Function to create symlink with better output
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

echo "🤖 Setting up Claude Code configuration..."
create_symlink "$DOTFILES_DIR/.claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md" "Claude global rules"

# Symlink every skill folder under .claude/skills/
for skill_dir in "$DOTFILES_DIR"/.claude/skills/*/; do
    skill_name=$(basename "$skill_dir")
    create_symlink "$skill_dir" "$HOME/.claude/skills/$skill_name" "Claude skill: $skill_name"
done

echo ""
echo "📦 Setting up required plugins..."

# Install superpowers plugin from official marketplace
claude plugin install superpowers@claude-plugins-official 2>/dev/null && \
    echo "  ✅ superpowers plugin installed" || \
    echo "  ⚠️  superpowers plugin already installed or failed"

echo ""
echo "  ℹ️  If plugin commands failed, run inside Claude Code:"
echo "     /plugin install superpowers@claude-plugins-official"

echo ""
echo "🎉 Claude Code setup complete!"
