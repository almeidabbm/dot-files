#!/bin/bash

# Read-only health check for dot-files.
# Verifies that every symlink this repo is supposed to create exists and
# resolves, that the shared AI rules + skills are projected into each tool,
# and that Superpowers is present for OpenCode. Makes NO changes.
# Exits non-zero if any check fails, so it is safe to use in scripts/CI.

DOTFILES_DIR="$HOME/Develop/dot-files"
SHARED=".ai/shared-instructions.md"

pass=0
fail=0

# A symlink is healthy when it is a link, resolves to a real file/dir, and
# its target contains the expected dot-files substring.
check_link() {
    local target="$1"
    local expected_substr="$2"
    local desc="$3"

    if [[ -L "$target" ]] && [[ -e "$target" ]] && [[ "$(readlink "$target")" == *"$expected_substr"* ]]; then
        echo "  ✅ $desc"
        ((pass++))
    elif [[ -L "$target" ]] && [[ ! -e "$target" ]]; then
        echo "  ❌ $desc — DANGLING ($target -> $(readlink "$target"))"
        ((fail++))
    else
        echo "  ❌ $desc — missing or not our symlink ($target)"
        ((fail++))
    fi
}

check_path() {
    local path="$1"
    local desc="$2"
    if [[ -e "$path" ]]; then
        echo "  ✅ $desc"
        ((pass++))
    else
        echo "  ❌ $desc — not found ($path)"
        ((fail++))
    fi
}

echo "🩺 dot-files doctor — read-only health check"
echo ""

echo "🐚 Shell & editor"
check_link "$HOME/.config/nvim/init.lua" "/dot-files/.config/nvim/init.lua" "Neovim init"
check_link "$HOME/.config/nvim/lua" "/dot-files/.config/nvim/lua" "Neovim lua config"
check_link "$HOME/.zshrc" "/dot-files/.zshrc" "Zsh config"
check_link "$HOME/.p10k.zsh" "/dot-files/.p10k.zsh" "Powerlevel10k theme"
check_link "$HOME/.default-npm-packages" "/dot-files/.default-npm-packages" "Default npm packages"
if [[ "$(uname)" == "Darwin" ]]; then
    check_link "$HOME/.fzf.mac.zsh" "/dot-files/.fzf.mac.zsh" "FZF config (macOS)"
else
    check_link "$HOME/.fzf.zsh" "/dot-files/.fzf.zsh" "FZF config (Linux)"
fi

echo ""
echo "📜 Shared AI rules (one source -> three tools)"
check_link "$HOME/.claude/CLAUDE.md" "$SHARED" "Claude   global rules"
check_link "$HOME/.codex/AGENTS.md" "$SHARED" "Codex    global rules"
check_link "$HOME/.config/opencode/AGENTS.md" "$SHARED" "OpenCode global rules"

echo ""
echo "🧩 Shared skills (per tool)"
for skill_dir in "$DOTFILES_DIR"/.ai/skills/*/; do
    [[ -d "$skill_dir" ]] || continue
    name=$(basename "$skill_dir")
    check_link "$HOME/.claude/skills/$name" "/dot-files/.ai/skills/$name" "Claude   skill: $name"
    check_link "$HOME/.codex/skills/$name" "/dot-files/.ai/skills/$name" "Codex    skill: $name"
    check_link "$HOME/.config/opencode/skills/$name" "/dot-files/.ai/skills/$name" "OpenCode skill: $name"
done

echo ""
echo "📦 Superpowers (OpenCode)"
check_path "$HOME/.config/opencode/superpowers" "Superpowers repo cloned"
check_link "$HOME/.config/opencode/plugins/superpowers.js" "/.config/opencode/superpowers" "Superpowers plugin"
check_link "$HOME/.config/opencode/skills/superpowers" "/.config/opencode/superpowers" "Superpowers skills"

echo ""
echo "────────────────────────────────────────"
echo "  $pass passed, $fail failed"
if [[ "$fail" -gt 0 ]]; then
    echo "  ⚠️  Run ./link.sh (or the relevant link-*.sh) to repair."
    exit 1
fi
echo "  🎉 All checks passed."
