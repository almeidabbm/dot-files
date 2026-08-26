#!/bin/bash

# Remove the canonical user-level MCP set this repo installs, plus leftover Graphite.

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
CURSOR_MCP="$HOME/.cursor/mcp.json"
OPENCODE_CONFIG="$HOME/.config/opencode/opencode.json"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"

remove_claude_mcp() {
    local name="$1"
    if (cd "$DOTFILES_DIR" && claude mcp get "$name" >/dev/null 2>&1); then
        (cd "$DOTFILES_DIR" && claude mcp remove "$name" -s user >/dev/null 2>&1) && \
            echo "  ✅ Removed $name from Claude Code" || \
            echo "  ⚠️  Failed to remove $name from Claude Code"
    else
        echo "  ℹ️  $name not found in Claude Code"
    fi
}

remove_codex_mcp() {
    local name="$1"
    if (cd "$DOTFILES_DIR" && codex mcp get "$name" >/dev/null 2>&1); then
        (cd "$DOTFILES_DIR" && codex mcp remove "$name" >/dev/null 2>&1) && \
            echo "  ✅ Removed $name from Codex" || \
            echo "  ⚠️  Failed to remove $name from Codex"
    else
        echo "  ℹ️  $name not found in Codex"
    fi
}

remove_json_mcp() {
    local path="$1"
    local root_key="$2"
    local name="$3"
    local label="$4"
    python3 - "$path" "$root_key" "$name" "$label" <<'PY'
import json, os, sys
path, root_key, name, label = sys.argv[1:5]
if not os.path.isfile(path):
    print(f"  ℹ️  {name} not found in {label}")
    raise SystemExit(0)
with open(path) as f:
    data = json.load(f)
servers = data.get(root_key) or {}
if name not in servers:
    print(f"  ℹ️  {name} not found in {label}")
    raise SystemExit(0)
del servers[name]
tmp = path + ".tmp"
with open(tmp, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
os.replace(tmp, path)
print(f"  ✅ Removed {name} from {label}")
PY
}

strip_stale_claude_settings_mcp() {
    if [[ ! -f "$CLAUDE_SETTINGS" ]]; then
        return
    fi
    python3 - "$CLAUDE_SETTINGS" <<'PY'
import json, os, sys
path = sys.argv[1]
with open(path) as f:
    data = json.load(f)
servers = data.get("mcpServers")
if not isinstance(servers, dict):
    raise SystemExit(0)
removed = [name for name in ("graphite", "linear") if name in servers]
if not removed:
    raise SystemExit(0)
for name in removed:
    del servers[name]
if not servers:
    del data["mcpServers"]
tmp = path + ".tmp"
with open(tmp, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
os.replace(tmp, path)
print("  ✅ Removed stale " + ", ".join(removed) + " from ~/.claude/settings.json")
PY
}

echo "🧹 Removing canonical MCP server configurations..."

echo ""
echo "🤖 Claude Code..."
remove_claude_mcp chrome-devtools
remove_claude_mcp linear
remove_claude_mcp linear-server
remove_claude_mcp pylon
remove_claude_mcp lightdash-docs
remove_claude_mcp graphite
strip_stale_claude_settings_mcp

echo ""
echo "🧠 Codex..."
remove_codex_mcp chrome-devtools
remove_codex_mcp linear
remove_codex_mcp pylon
remove_codex_mcp lightdash-docs
remove_codex_mcp graphite

echo ""
echo "⚡ OpenCode..."
remove_json_mcp "$OPENCODE_CONFIG" mcp chrome-devtools OpenCode
remove_json_mcp "$OPENCODE_CONFIG" mcp linear OpenCode
remove_json_mcp "$OPENCODE_CONFIG" mcp pylon OpenCode
remove_json_mcp "$OPENCODE_CONFIG" mcp lightdash-docs OpenCode
remove_json_mcp "$OPENCODE_CONFIG" mcp graphite OpenCode

echo ""
echo "🖥️  Cursor..."
remove_json_mcp "$CURSOR_MCP" mcpServers chrome-devtools Cursor
remove_json_mcp "$CURSOR_MCP" mcpServers pylon Cursor
remove_json_mcp "$CURSOR_MCP" mcpServers lightdash-docs Cursor
remove_json_mcp "$CURSOR_MCP" mcpServers linear Cursor
remove_json_mcp "$CURSOR_MCP" mcpServers graphite Cursor

echo ""
echo "🎉 MCP cleanup complete!"
