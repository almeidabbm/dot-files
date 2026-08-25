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
            echo "  ⚠️  Skipping: $target (points to $link_target, not opencode)"
        fi
    elif [[ -e "$target" ]]; then
        echo "  ⚠️  Skipping: $target (exists but is not a symlink)"
    else
        echo "  ✅ Already clean: $target"
    fi
}

echo "🗑️  Removing OpenCode configuration..."

agents_link="$HOME/.config/opencode/AGENTS.md"
if [[ -L "$agents_link" ]] && [[ "$(readlink "$agents_link")" == *"/.ai/shared-instructions.md" ]]; then
    echo "  🗑️  Removing: $agents_link -> $(readlink "$agents_link")"
    rm "$agents_link"
elif [[ -e "$agents_link" ]]; then
    echo "  ⚠️  Skipping: $agents_link (exists but is not our symlink)"
else
    echo "  ✅ Already clean: $agents_link"
fi

echo ""
echo "👤 Removing personal skills from dot-files..."
if [[ -d "$HOME/.config/opencode/skills" ]]; then
    for link in "$HOME/.config/opencode/skills"/*; do
        [[ -L "$link" ]] || continue
        if [[ "$(readlink "$link")" == *"$DOTFILES_DIR/.ai/skills"* ]]; then
            remove_symlink "$link" "Skill: $(basename "$link")"
        fi
    done
fi

echo ""
echo "🎉 OpenCode configuration removed!"
