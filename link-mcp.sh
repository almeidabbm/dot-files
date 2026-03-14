#!/bin/bash

# Standalone script to install and configure MCP servers at system level.
# Installs Chrome DevTools MCP for both Claude Code and OpenCode.

DOTFILES_DIR="$HOME/Develop/dot-files"

install_npm_global() {
    local package="$1"
    if npm list -g "$package" >/dev/null 2>&1; then
        echo "  ✅ $package already installed"
    else
        npm install -g "$package" 2>/dev/null && \
            echo "  ✅ $package installed" || \
            echo "  ⚠️  Failed to install $package"
    fi
}

add_claude_mcp() {
    local name="$1"
    shift
    
    if claude mcp list 2>/dev/null | grep -q "^$name$"; then
        echo "  ℹ️  $name already configured in Claude Code"
    else
        claude mcp add -s user "$name" -- "$@" 2>/dev/null && \
            echo "  ✅ Added $name to Claude Code" || \
            echo "  ⚠️  Failed to add $name to Claude Code"
    fi
}

add_opencode_mcp() {
    local name="$1"
    local package="$2"
    
    local opencode_config="$HOME/.config/opencode/opencode.json"
    
    mkdir -p "$(dirname "$opencode_config")"
    
    if [ -f "$opencode_config" ]; then
        if grep -q "\"$name\"" "$opencode_config" 2>/dev/null; then
            echo "  ℹ️  $name already configured in OpenCode"
            return
        fi
    fi
    
    local mcp_json="{\"$name\": {\"type\": \"local\", \"command\": [\"npx\", \"-y\", \"$package\"], \"enabled\": true}}"
    
    if [ -f "$opencode_config" ] && [ -s "$opencode_config" ]; then
        jq -s '.[0] * .[1]' "$opencode_config" <(echo "{\"mcp\": $mcp_json}") > /tmp/opencode_mcp_$$.json && \
            mv /tmp/opencode_mcp_$$.json "$opencode_config"
    else
        echo "{\"mcp\": $mcp_json}" > "$opencode_config"
    fi
    
    echo "  ✅ Added $name to OpenCode"
}

echo "🔧 Setting up MCP servers..."

echo ""
echo "📦 Installing NPM packages globally..."
install_npm_global "chrome-devtools-mcp"

echo ""
echo "🤖 Configuring MCP servers for Claude Code..."
add_claude_mcp chrome-devtools npx -y chrome-devtools-mcp

echo ""
echo "⚡ Configuring MCP servers for OpenCode..."
add_opencode_mcp chrome-devtools "chrome-devtools-mcp"

echo ""
echo "📝 Next steps:"
echo "   - Restart Claude Code and OpenCode to load MCP servers"
echo ""
echo "🎉 MCP setup complete!"
