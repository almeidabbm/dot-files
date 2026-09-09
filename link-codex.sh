#!/bin/bash

# Standalone script to symlink only Codex configuration.
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

echo "🧠 Setting up Codex configuration..."
remove_agent_memory_cli
create_symlink "$DOTFILES_DIR/.ai/shared-instructions.md" "$HOME/.codex/AGENTS.md" "Codex global rules"

echo ""
echo "🧩 Skills (~/.agents/skills, read by Codex and OpenCode)"
prune_dangling_links "$HOME/.agents/skills" "shared skill"
prune_dangling_links "$HOME/.codex/skills" "legacy Codex skill"
for skill in "$DOTFILES_DIR"/.ai/skills/*/; do
    name="$(basename "$skill")"
    create_symlink "${skill%/}" "$HOME/.agents/skills/$name" "Skill $name"
done

echo ""
echo "👥 Worker agents (~/.codex/agents)"
prune_dangling_links "$HOME/.codex/agents" "Codex agent"
for agent in "$DOTFILES_DIR"/.ai/agents/codex/*.toml; do
    create_symlink "$agent" "$HOME/.codex/agents/$(basename "$agent")" "Agent $(basename "$agent" .toml)"
done
create_symlink "$DOTFILES_DIR/.ai/agents/roles" "$HOME/.agents/roles" "Role briefs for CLI workers"

echo ""
echo "  ℹ️  Restart Codex if it is already open so it reloads AGENTS.md"
echo ""
echo "🎉 Codex setup complete!"
