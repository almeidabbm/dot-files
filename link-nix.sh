#!/bin/bash
set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.config/nix"
mkdir -p "$HOME/.config"

if [[ -e "$TARGET" && ! -L "$TARGET" ]]; then
    BACKUP="$(mktemp -d "$HOME/.config/nix.backup.XXXXXX")"
    mv "$TARGET" "$BACKUP/nix"
    echo "Backed up existing Nix configuration to $BACKUP/nix"
fi

ln -nfs "$DOTFILES_DIR/.config/nix" "$TARGET"
echo "Linked $TARGET -> $DOTFILES_DIR/.config/nix"
