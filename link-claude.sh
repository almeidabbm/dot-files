#!/bin/bash

# Standalone script to symlink only Claude Code configuration.
# Can be run independently without affecting other dotfiles.

DOTFILES_DIR="$HOME/Develop/dot-files"

# Function to create symlink with better output
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

# Register the git trunk guard as a PreToolUse(Bash) hook in the global
# settings. Uses jq to merge idempotently so it never clobbers Claude Code's
# own managed settings (theme, plugins, other hooks). A backup is kept.
install_git_guard_hook() {
    local settings="$HOME/.claude/settings.json"
    local hook_cmd="$DOTFILES_DIR/.ai/hooks/guard-git-trunk.sh"
    local marker="guard-git-trunk.sh"

    command -v jq >/dev/null 2>&1 || { echo "  ⚠️  jq not found; skipping git guard hook"; return; }
    [[ -f "$settings" ]] || echo '{}' > "$settings"

    local count
    count=$(jq --arg m "$marker" '[.. | .command? // empty | select(contains($m))] | length' "$settings" 2>/dev/null || echo 0)
    if [[ "${count:-0}" -gt 0 ]]; then
        echo "  ℹ️  Git guard hook already installed"
        return
    fi

    local tmp
    tmp=$(mktemp)
    if jq --arg cmd "$hook_cmd" \
        '.hooks.PreToolUse = ((.hooks.PreToolUse // []) + [{"matcher":"Bash","hooks":[{"type":"command","command":$cmd}]}])' \
        "$settings" > "$tmp" 2>/dev/null && jq empty "$tmp" 2>/dev/null; then
        cp "$settings" "$settings.dotfiles.bak"
        mv "$tmp" "$settings"
        echo "  ✅ Installed git guard hook (blocks commit/push to trunk)"
    else
        rm -f "$tmp"
        echo "  ❌ Failed to install git guard hook (settings.json left unchanged)"
    fi
}

echo "🤖 Setting up Claude Code configuration..."
create_symlink "$DOTFILES_DIR/.ai/shared-instructions.md" "$HOME/.claude/CLAUDE.md" "Claude global rules"

# Symlink every shared skill folder under .ai/skills/
for skill_dir in "$DOTFILES_DIR"/.ai/skills/*/; do
    [[ -d "$skill_dir" ]] || continue
    skill_name=$(basename "$skill_dir")
    create_symlink "$skill_dir" "$HOME/.claude/skills/$skill_name" "Claude skill: $skill_name"
done

echo ""
echo "📦 Setting up required plugins..."

# Install superpowers plugin from official marketplace
claude plugin install superpowers@claude-plugins-official 2>/dev/null && \
    echo "  ✅ superpowers plugin installed" || \
    echo "  ⚠️  superpowers plugin already installed or failed"

echo ""
echo "  ℹ️  If plugin commands failed, run inside Claude Code:"
echo "     /plugin install superpowers@claude-plugins-official"

echo ""
echo "🪝 Installing git guard hook..."
install_git_guard_hook

echo ""
echo "🎉 Claude Code setup complete!"
