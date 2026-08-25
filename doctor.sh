#!/bin/bash

# Read-only health check for dot-files.
# Verifies that every symlink this repo is supposed to create exists and
# resolves. Makes NO changes.
# Exits non-zero if any check fails, so it is safe to use in scripts/CI.

DOTFILES_DIR="$HOME/Develop/dot-files"
SHARED=".ai/shared-instructions.md"

pass=0
fail=0

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

check_absent() {
    local target="$1"
    local desc="$2"

    if [[ -e "$target" ]] || [[ -L "$target" ]]; then
        echo "  ❌ $desc — still present ($target); run link-*.sh to clear"
        ((fail++))
    else
        echo "  ✅ $desc"
        ((pass++))
    fi
}

echo "🩺 dot-files doctor — read-only health check"
echo ""

echo "🐚 Shell & editor"
check_link "$HOME/.config/nvim/init.lua" "/dot-files/.config/nvim/init.lua" "Neovim init"
check_link "$HOME/.config/tmux/tmux.conf" "/dot-files/.config/tmux/tmux.conf" "tmux config"
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
check_absent "$HOME/.local/bin/agent-memory" "Legacy agent-memory CLI absent"

echo ""
echo "────────────────────────────────────────"
echo "  $pass passed, $fail failed"
if [[ "$fail" -gt 0 ]]; then
    echo "  ⚠️  Run ./link.sh (or the relevant link-*.sh) to repair."
    exit 1
fi
echo "  🎉 All checks passed."
