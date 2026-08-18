#!/bin/bash

echo "🧹 Removing MCP server configurations..."

DOTFILES_DIR="$HOME/Develop/dot-files"

remove_claude_mcp() {
    local name="$1"
    
    if (cd "$DOTFILES_DIR" && claude mcp get "$name" >/dev/null 2>&1); then
        (cd "$DOTFILES_DIR" && claude mcp remove "$name" -s user 2>/dev/null) && \
            echo "  ✅ Removed $name from Claude Code" || \
            echo "  ⚠️  Failed to remove $name from Claude Code"
    else
        echo "  ℹ️  $name not found in Claude Code"
    fi
}

remove_codex_mcp() {
    local name="$1"

    if (cd "$DOTFILES_DIR" && codex mcp get "$name" >/dev/null 2>&1); then
        (cd "$DOTFILES_DIR" && codex mcp remove "$name" 2>/dev/null) && \
            echo "  ✅ Removed $name from Codex" || \
            echo "  ⚠️  Failed to remove $name from Codex"
    else
        echo "  ℹ️  $name not found in Codex"
    fi
}

remove_opencode_mcp() {
    local name="$1"
    
    local opencode_config="$HOME/.config/opencode/opencode.json"
    
    if [ -f "$opencode_config" ]; then
        if grep -q "\"$name\"" "$opencode_config" 2>/dev/null; then
            local temp_file=$(mktemp)
            jq "del(.mcp.\"$name\")" "$opencode_config" > "$temp_file" && \
                mv "$temp_file" "$opencode_config" && \
                echo "  ✅ Removed $name from OpenCode" || \
                echo "  ⚠️  Failed to remove $name from OpenCode"
        else
            echo "  ℹ️  $name not found in OpenCode"
        fi
    else
        echo "  ℹ️  OpenCode config not found"
    fi
}

echo ""
echo "🤖 Removing MCP servers from Claude Code..."
remove_claude_mcp chrome-devtools

echo ""
echo "🧠 Removing MCP servers from Codex..."
remove_codex_mcp chrome-devtools

echo ""
echo "⚡ Removing MCP servers from OpenCode..."
remove_opencode_mcp chrome-devtools

echo ""
echo "🎉 MCP cleanup complete!"
