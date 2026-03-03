#!/bin/bash

# Script to unlink and remove OpenCode superpowers configuration.

remove_symlink() {
    local target="$1"
    local description="$2"

    if [[ -L "$target" ]]; then
        local link_target=$(readlink "$target")
        if [[ "$link_target" == *"$HOME/.config/opencode"* ]]; then
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

echo "🗑️  Removing OpenCode superpowers..."

remove_symlink "$HOME/.config/opencode/plugins/superpowers.js" "Superpowers plugin"
remove_symlink "$HOME/.config/opencode/skills/superpowers" "Superpowers skills"

echo ""
echo "👤 Removing personal skills from dot-files..."
for skill in "$HOME/Develop/dot-files/.claude/skills"/*; do
    if [[ -d "$skill" ]]; then
        skill_name=$(basename "$skill")
        remove_symlink "$HOME/.config/opencode/skills/$skill_name" "Skill: $skill_name"
    fi
done

if [[ -d "$HOME/.config/opencode/superpowers" ]]; then
    echo "  🗑️  Removing superpowers repository..."
    rm -rf "$HOME/.config/opencode/superpowers"
else
    echo "  ✅ Already clean: superpowers repository"
fi

echo ""
echo "🎉 OpenCode superpowers removed!"
