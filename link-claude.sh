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
create_symlink "$DOTFILES_DIR/.claude/skills/worktree-setup" "$HOME/.claude/skills/worktree-setup" "Claude worktree skill"
create_symlink "$DOTFILES_DIR/.claude/skills/review-respond" "$HOME/.claude/skills/review-respond" "Claude review-respond skill"
create_symlink "$DOTFILES_DIR/.claude/skills/code-review" "$HOME/.claude/skills/code-review" "Claude code-review skill"

echo ""
echo "🎉 Claude Code setup complete!"
