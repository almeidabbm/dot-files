#!/bin/bash

# Standalone script to remove only Codex symlinks.

DOTFILES_DIR="$HOME/Develop/dot-files"
shopt -s nullglob

remove_symlink() {
    local target="$1"
    local description="$2"

    if [[ -L "$target" ]]; then
        local link_target
        link_target=$(readlink "$target")
        if [[ "$link_target" == *"$DOTFILES_DIR"* ]]; then
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

# Remove every link in a directory that points into this repo's .ai/<subdir>/.
remove_repo_links() {
    local dir="$1"
    local subdir="$2"
    local label="$3"
    [[ -d "$dir" ]] || return 0
    local link
    for link in "$dir"/*; do
        [[ -L "$link" ]] || continue
        if [[ "$(readlink "$link")" == "$DOTFILES_DIR/.ai/$subdir/"* ]]; then
            remove_symlink "$link" "$label: $(basename "$link")"
        fi
    done
}

echo "🧹 Cleaning up Codex symlinks..."
remove_symlink "$HOME/.codex/AGENTS.md" "Codex global rules"
remove_repo_links "$HOME/.codex/skills" "skills" "Legacy Codex skill"
remove_repo_links "$HOME/.codex/agents" "agents" "Codex agent"

echo ""
echo "  ℹ️  Shared ~/.agents links stay until unlink.sh removes them"
echo ""
echo "🎉 Codex cleanup complete!"
