#!/bin/bash

# Standalone script to remove only Codex symlinks.

DOTFILES_DIR="$HOME/Develop/dot-files"

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

echo "🧹 Cleaning up Codex symlinks..."
remove_symlink "$HOME/.codex/AGENTS.md" "Codex global rules"

if [[ -d "$HOME/.codex/skills" ]]; then
    for link in "$HOME/.codex/skills"/*; do
        [[ -L "$link" ]] || continue
        if [[ "$(readlink "$link")" == *"$DOTFILES_DIR/.ai/skills"* ]]; then
            remove_symlink "$link" "Codex skill: $(basename "$link")"
        fi
    done
fi

echo ""
echo "🎉 Codex cleanup complete!"
