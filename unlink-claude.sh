#!/bin/bash

# Standalone script to remove only Claude Code symlinks.

# Function to remove symlink if it exists and points to dot-files
remove_symlink() {
    local target="$1"
    local description="$2"

    if [[ -L "$target" ]]; then
        local link_target=$(readlink "$target")
        if [[ "$link_target" == *"$HOME/Develop/dot-files"* ]]; then
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
remove_symlink "$HOME/.claude/skills/code-review" "Claude code-review skill"

echo ""
echo "🎉 Claude Code cleanup complete!"
