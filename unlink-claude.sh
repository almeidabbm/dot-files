#!/bin/bash

# Standalone script to remove only Claude Code symlinks.

DOTFILES_DIR="$HOME/Develop/dot-files"

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

# Remove the git trunk guard PreToolUse hook from the global settings,
# leaving every other hook and setting untouched.
remove_git_guard_hook() {
    local settings="$HOME/.claude/settings.json"
    local marker="guard-git-trunk.sh"

    command -v jq >/dev/null 2>&1 || return
    [[ -f "$settings" ]] || return

    local count
    count=$(jq --arg m "$marker" '[.. | .command? // empty | select(contains($m))] | length' "$settings" 2>/dev/null || echo 0)
    if [[ "${count:-0}" -eq 0 ]]; then
        echo "  ✅ Git guard hook already absent"
        return
    fi

    local tmp
    tmp=$(mktemp)
    if jq --arg m "$marker" \
        '(.hooks.PreToolUse) |= (map(select(((.hooks // []) | map(.command // "") | any(contains($m))) | not)))' \
        "$settings" > "$tmp" 2>/dev/null && jq empty "$tmp" 2>/dev/null; then
        mv "$tmp" "$settings"
        echo "  🗑️  Removed git guard hook"
    else
        rm -f "$tmp"
        echo "  ⚠️  Failed to remove git guard hook (settings.json left unchanged)"
    fi
}

echo "🤖 Cleaning up Claude Code symlinks..."
remove_symlink "$HOME/.claude/CLAUDE.md" "Claude global rules"
remove_git_guard_hook

# Remove every shared skill folder symlinked into Claude
for skill_dir in "$DOTFILES_DIR"/.ai/skills/*/; do
    [[ -d "$skill_dir" ]] || continue
    skill_name=$(basename "$skill_dir")
    remove_symlink "$HOME/.claude/skills/$skill_name" "Claude skill: $skill_name"
done

echo ""
echo "🎉 Claude Code cleanup complete!"
