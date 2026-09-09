#!/bin/bash

# Script to unlink and remove OpenCode configuration.

DOTFILES_DIR="$HOME/Develop/dot-files"

remove_symlink() {
    local target="$1"
    local description="$2"

    if [[ -L "$target" ]]; then
        local link_target
        link_target=$(readlink "$target")
        if [[ "$link_target" == *"$DOTFILES_DIR"* ]]; then
            echo "  🗑️  Removing: $target -> $link_target"
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

# Remove every link in a directory that points into this repo's .ai/<subdir>/.
remove_repo_links() {
    local dir="$1"
    local subdir="$2"
    local label="$3"
    [[ -d "$dir" ]] || return 0
    local link
    for link in "$dir"/*; do
        [[ -L "$link" ]] || continue
        if [[ "$(readlink "$link")" == "$DOTFILES_DIR/.ai/$subdir"* ]]; then
            remove_symlink "$link" "$label: $(basename "$link")"
        fi
    done
}

echo "🗑️  Removing OpenCode configuration..."
remove_symlink "$HOME/.config/opencode/AGENTS.md" "OpenCode global rules"
remove_repo_links "$HOME/.agents/skills" "skills" "Shared skill"
remove_repo_links "$HOME/.config/opencode/skills" "skills" "Legacy OpenCode skill"
remove_repo_links "$HOME/.config/opencode/agents" "agents" "OpenCode agent"
remove_symlink "$HOME/.agents/roles" "Role briefs for CLI workers"

echo ""
echo "🎉 OpenCode configuration removed!"
