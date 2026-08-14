#!/bin/bash

# Install the remote sandbox dispatcher on PATH.

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
source_path="$DOTFILES_DIR/agent-run/bin/agent-run"
target_path="$HOME/.local/bin/agent-run"

mkdir -p "$(dirname "$target_path")"

if ln -nfs "$source_path" "$target_path" 2>/dev/null; then
    echo "  ✅ Agent run CLI: $target_path -> $source_path"
else
    echo "  ❌ Failed to link agent run CLI: $target_path"
    exit 1
fi

# agent-run needs these to read templates; agent-memory is stdlib-only.
for module in jsonschema yaml; do
    python3 -c "import $module" 2>/dev/null || \
        echo "  ⚠️  python3 module '$module' is missing (pip install jsonschema pyyaml)"
done
