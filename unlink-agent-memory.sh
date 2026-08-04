#!/bin/bash

# Remove only the agent-memory symlink managed by this repository.

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
target_path="$HOME/.local/bin/agent-memory"

if [[ -L "$target_path" ]] && [[ "$(readlink "$target_path")" == "$DOTFILES_DIR/.ai/bin/agent-memory" ]]; then
    rm "$target_path"
    echo "  🗑️  Removed agent memory CLI"
elif [[ -e "$target_path" ]]; then
    echo "  ⚠️  Skipping agent memory CLI (not our symlink)"
else
    echo "  ✅ Agent memory CLI already absent"
fi
