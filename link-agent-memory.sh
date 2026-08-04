#!/bin/bash

# Install the deterministic workflow-state CLI shared by every coding agent.

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
source_path="$DOTFILES_DIR/.ai/bin/agent-memory"
target_path="$HOME/.local/bin/agent-memory"

mkdir -p "$(dirname "$target_path")"

if ln -nfs "$source_path" "$target_path" 2>/dev/null; then
    echo "  ✅ Agent memory CLI: $target_path -> $source_path"
else
    echo "  ❌ Failed to link agent memory CLI: $target_path"
    exit 1
fi
