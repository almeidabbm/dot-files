#!/bin/bash

# Remove only the agent-run symlink managed by this repository.

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
target_path="$HOME/.local/bin/agent-run"

if [[ -L "$target_path" ]] && [[ "$(readlink "$target_path")" == "$DOTFILES_DIR/agent-run/bin/agent-run" ]]; then
    rm "$target_path"
    echo "  🗑️  Removed agent run CLI"
elif [[ -e "$target_path" ]]; then
    echo "  ⚠️  Skipping agent run CLI (not our symlink)"
else
    echo "  ✅ Agent run CLI already absent"
fi
