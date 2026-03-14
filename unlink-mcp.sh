#!/bin/bash

echo "🧹 Removing MCP server configurations..."

DOTFILES_DIR="$HOME/Develop/dot-files"

remove_claude_mcp() {
    local name="$1"
    
    if claude mcp list 2>/dev/null | grep -q "^$name$"; then
        claude mcp remove "$name" 2>/dev/null && \
            echo "  ✅ Removed $name from Claude Code" || \
            echo "  ⚠️  Failed to remove $name from Claude Code"
    else
        echo "  ℹ️  $name not found in Claude Code"
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
echo "⚡ Removing MCP servers from OpenCode..."
remove_opencode_mcp chrome-devtools

echo ""
echo "🎉 MCP cleanup complete!"
