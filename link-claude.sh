#!/bin/bash

# Standalone script to symlink only Claude Code configuration.
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

# Drop links into this repo's .ai/ whose source no longer exists (renamed or removed).
prune_dangling_links() {
    local dir="$1"
    local label="$2"
    [[ -d "$dir" ]] || return 0
    local link
    for link in "$dir"/*; do
        [[ -L "$link" ]] || continue
        if [[ "$(readlink "$link")" == "$DOTFILES_DIR/.ai/"* ]] && [[ ! -e "$link" ]]; then
            rm "$link"
            echo "  🗑️  Removed stale $label: $(basename "$link")"
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

echo "🤖 Setting up Claude Code configuration..."
remove_agent_memory_cli
create_symlink "$DOTFILES_DIR/.ai/shared-instructions.md" "$HOME/.claude/CLAUDE.md" "Claude global rules"

echo ""
echo "🧩 Skills (~/.claude/skills)"
prune_dangling_links "$HOME/.claude/skills" "Claude skill"
for skill in "$DOTFILES_DIR"/.ai/skills/*/; do
    name="$(basename "$skill")"
    create_symlink "${skill%/}" "$HOME/.claude/skills/$name" "Skill $name"
done

echo ""
echo "👥 Worker agents (~/.claude/agents)"
prune_dangling_links "$HOME/.claude/agents" "Claude agent"
for agent in "$DOTFILES_DIR"/.ai/agents/claude/*.md; do
    create_symlink "$agent" "$HOME/.claude/agents/$(basename "$agent")" "Agent $(basename "$agent" .md)"
done
create_symlink "$DOTFILES_DIR/.ai/agents/roles" "$HOME/.agents/roles" "Role briefs for CLI workers"

echo ""
echo "🎉 Claude Code setup complete!"
