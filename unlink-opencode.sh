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
for skill in "$HOME/Develop/dot-files/.ai/skills"/*; do
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
