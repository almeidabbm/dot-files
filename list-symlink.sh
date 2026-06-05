#!/bin/bash

# Lists all active symlinks managed by this repo.

DOTFILES_DIR="$HOME/Develop/dot-files"

targets=(
    "$HOME/.config/nvim/init.lua|Neovim init"
    "$HOME/.config/nvim/lua|Neovim Lua config"
    "$HOME/.zshrc|Zsh config"
    "$HOME/.p10k.zsh|Powerlevel10k theme"
    "$HOME/.default-npm-packages|Default NPM packages"
    "$HOME/.fzf.zsh|FZF config (Linux)"
    "$HOME/.fzf.mac.zsh|FZF config (macOS)"
)

if [[ -f "$DOTFILES_DIR/.ai/shared-instructions.md" ]]; then
    targets+=("$HOME/.claude/CLAUDE.md|Claude global rules")
    targets+=("$HOME/.codex/AGENTS.md|Codex global rules")
fi

targets+=("$HOME/.config/opencode/plugins/superpowers.js|OpenCode superpowers plugin")
targets+=("$HOME/.config/opencode/skills/superpowers|OpenCode superpowers skills")

for skill_dir in "$DOTFILES_DIR"/.ai/skills/*/; do
    [[ -d "$skill_dir" ]] || continue
    skill_name=$(basename "$skill_dir")
    targets+=("$HOME/.claude/skills/$skill_name|Claude skill: $skill_name")
    targets+=("$HOME/.codex/skills/$skill_name|Codex skill: $skill_name")
    targets+=("$HOME/.config/opencode/skills/$skill_name|OpenCode personal skill: $skill_name")
done

echo ""
echo "🔗 Dot-files symlinks"
echo ""

found=0
missing=0

for entry in "${targets[@]}"; do
    target="${entry%%|*}"
    description="${entry##*|}"
    short_target="${target/#$HOME/~}"

    if [[ -L "$target" ]]; then
        link_target=$(readlink "$target")
        if [[ "$link_target" == *"$DOTFILES_DIR"* ]]; then
            echo "  ✅ $description"
            echo "     $short_target"
            ((found++))
        fi
    elif [[ -e "$target" ]]; then
        echo "  ⚠️  $description (exists but not a symlink)"
        echo "     $short_target"
        ((missing++))
    else
        echo "  ❌ $description (not linked)"
        echo "     $short_target"
        ((missing++))
    fi
done

echo ""
echo "───────────────────────────────"
echo "  $found linked · $missing not linked"
echo ""
