#!/bin/bash
set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.config/nix"

if [[ -L "$TARGET" && "$(readlink "$TARGET")" == "$DOTFILES_DIR/.config/nix" ]]; then
    rm "$TARGET"
    echo "Removed Nix configuration link: $TARGET"
fi
