#!/bin/bash

# Standalone script to remove only Claude Code symlinks.

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

echo "🤖 Cleaning up Claude Code symlinks..."
remove_symlink "$HOME/.claude/CLAUDE.md" "Claude global rules"

# Remove any leftover skill links that pointed into this repo's .ai/skills/
if [[ -d "$HOME/.claude/skills" ]]; then
    for link in "$HOME/.claude/skills"/*; do
        [[ -L "$link" ]] || continue
        if [[ "$(readlink "$link")" == *"$DOTFILES_DIR/.ai/skills"* ]]; then
            remove_symlink "$link" "Claude skill: $(basename "$link")"
        fi
    done
fi

echo ""
echo "🎉 Claude Code cleanup complete!"
