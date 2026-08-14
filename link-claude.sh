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
"$DOTFILES_DIR/link-agent-memory.sh"
"$DOTFILES_DIR/link-agent-run.sh"
create_symlink "$DOTFILES_DIR/.ai/shared-instructions.md" "$HOME/.claude/CLAUDE.md" "Claude global rules"

# Symlink every shared skill folder under .ai/skills/
for skill_dir in "$DOTFILES_DIR"/.ai/skills/*/; do
    [[ -d "$skill_dir" ]] || continue
    skill_name=$(basename "$skill_dir")
    create_symlink "$skill_dir" "$HOME/.claude/skills/$skill_name" "Claude skill: $skill_name"
done

echo ""
echo "🎉 Claude Code setup complete!"
