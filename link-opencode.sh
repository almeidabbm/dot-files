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

remove_repo_skill_links() {
    local skills_dir="$1"
    local label="$2"
    [[ -d "$skills_dir" ]] || return 0
    local link
    for link in "$skills_dir"/*; do
        [[ -L "$link" ]] || continue
        if [[ "$(readlink "$link")" == *"$DOTFILES_DIR/.ai/skills"* ]]; then
            rm "$link"
            echo "  🗑️  Removed stale $label skill: $(basename "$link")"
        fi
    done
}

remove_agent_memory_cli() {
    local target="$HOME/.local/bin/agent-memory"
    if [[ -L "$target" ]] && [[ "$(readlink "$target")" == *"$DOTFILES_DIR/.ai/bin/agent-memory"* ]]; then
        rm "$target"
        echo "  🗑️  Removed legacy agent-memory CLI"
    fi
}

echo "⚡ Setting up OpenCode configuration..."
remove_agent_memory_cli

echo ""
echo "🔗 Creating symlinks..."

create_symlink "$DOTFILES_DIR/.ai/shared-instructions.md" \
               "$HOME/.config/opencode/AGENTS.md" \
               "OpenCode global rules"
remove_repo_skill_links "$HOME/.config/opencode/skills" "OpenCode"

echo ""
echo "  ℹ️  Restart OpenCode to reload AGENTS.md"
echo ""
echo "🎉 OpenCode setup complete!"
