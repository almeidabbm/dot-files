#!/bin/bash

# Standalone script to symlink only Codex configuration.
# Can be run independently without affecting other dotfiles.

DOTFILES_DIR="$HOME/Develop/dot-files"

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

echo "🧠 Setting up Codex configuration..."
create_symlink "$DOTFILES_DIR/.ai/shared-instructions.md" "$HOME/.codex/AGENTS.md" "Codex global rules"

for skill_dir in "$DOTFILES_DIR"/.ai/skills/*/; do
    [[ -d "$skill_dir" ]] || continue
    skill_name=$(basename "$skill_dir")
    create_symlink "$skill_dir" "$HOME/.codex/skills/$skill_name" "Codex skill: $skill_name"
done

echo ""
echo "📦 Setting up required plugins..."

codex plugin add superpowers@openai-curated 2>/dev/null && \
    echo "  ✅ superpowers plugin installed" || \
    echo "  ⚠️  superpowers plugin already installed or failed"

echo ""
echo "  ℹ️  If plugin commands failed, run:"
echo "     codex plugin add superpowers@openai-curated"
echo ""
echo "  ℹ️  Restart Codex if it is already open so it reloads AGENTS.md and skills"
echo ""
echo "🎉 Codex setup complete!"
