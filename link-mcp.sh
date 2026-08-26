#!/bin/bash

# Install the canonical user-level MCP set for Claude Code, Codex, OpenCode, and Cursor.
#
#   chrome-devtools   stdio   inspect a running browser
#   linear            http    tickets (Cursor uses the Linear plugin instead)
#   pylon             http    support
#   lightdash-docs    http    product docs
#
# Cursor does not read Claude MCP paths. GitHub stays on `gh` / `gh stack`.
# Graphite is removed wherever this script finds it.

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
CURSOR_MCP="$HOME/.cursor/mcp.json"
OPENCODE_CONFIG="$HOME/.config/opencode/opencode.json"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"

CHROME_DEVTOOLS_PACKAGE="chrome-devtools-mcp@latest"
CHROME_DEVTOOLS_ARGS=(-y "$CHROME_DEVTOOLS_PACKAGE" --isolated)

LINEAR_URL="https://mcp.linear.app/mcp"
PYLON_URL="https://mcp.usepylon.com/"
LIGHTDASH_DOCS_URL="https://docs.lightdash.com/mcp"

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

claude_has_mcp() {
    local name="$1"
    (cd "$DOTFILES_DIR" && claude mcp get "$name" >/dev/null 2>&1)
}

codex_has_mcp() {
    local name="$1"
    (cd "$DOTFILES_DIR" && codex mcp get "$name" >/dev/null 2>&1)
}

add_claude_stdio() {
    local name="$1"
    shift

    if claude_has_mcp "$name"; then
        (cd "$DOTFILES_DIR" && claude mcp remove "$name" -s user >/dev/null 2>&1) || true
    fi
    if (cd "$DOTFILES_DIR" && claude mcp add -s user "$name" -- "$@"); then
        echo "  ✅ $name (Claude Code)"
    else
        echo "  ⚠️  Failed to add $name to Claude Code"
    fi
}

add_claude_http() {
    local name="$1"
    local url="$2"
    shift 2

    local existing
    for existing in "$name" "$@"; do
        if claude_has_mcp "$existing"; then
            echo "  ℹ️  $existing already configured in Claude Code"
            return
        fi
    done

    if (cd "$DOTFILES_DIR" && claude mcp add -s user --transport http "$name" "$url"); then
        echo "  ✅ $name (Claude Code)"
    else
        echo "  ⚠️  Failed to add $name to Claude Code"
    fi
}

add_codex_stdio() {
    local name="$1"
    shift

    if codex_has_mcp "$name"; then
        (cd "$DOTFILES_DIR" && codex mcp remove "$name" >/dev/null 2>&1) || true
    fi
    if (cd "$DOTFILES_DIR" && codex mcp add "$name" -- "$@"); then
        echo "  ✅ $name (Codex)"
    else
        echo "  ⚠️  Failed to add $name to Codex"
    fi
}

add_codex_http() {
    local name="$1"
    local url="$2"

    if codex_has_mcp "$name"; then
        echo "  ℹ️  $name already configured in Codex"
        return
    fi
    if (cd "$DOTFILES_DIR" && codex mcp add "$name" --url "$url"); then
        echo "  ✅ $name (Codex)"
    else
        echo "  ⚠️  Failed to add $name to Codex"
    fi
}

upsert_json_mcp() {
    python3 - "$@" <<'PY'
import json, os, sys

path, kind, name = sys.argv[1], sys.argv[2], sys.argv[3]
payload = json.loads(sys.argv[4])
root_key = sys.argv[5]
os.makedirs(os.path.dirname(path), exist_ok=True)
if os.path.isfile(path) and os.path.getsize(path) > 0:
    with open(path) as f:
        data = json.load(f)
else:
    data = {}
servers = data.setdefault(root_key, {})
servers[name] = payload
tmp = path + ".tmp"
with open(tmp, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
os.replace(tmp, path)
print(kind)
PY
}

add_opencode_stdio() {
    local name="$1"
    local package="$2"
    local extra="$3"
    local payload
    payload="$(python3 -c 'import json,sys; print(json.dumps({"type":"local","command":["npx","-y",sys.argv[1],*sys.argv[2].split()],"enabled":True}))' "$package" "$extra")"
    local result
    result="$(upsert_json_mcp "$OPENCODE_CONFIG" "upserted" "$name" "$payload" "mcp")"
    echo "  ✅ $name (OpenCode, $result)"
}

add_opencode_http() {
    local name="$1"
    local url="$2"
    local payload
    payload="$(python3 -c 'import json,sys; print(json.dumps({"type":"remote","url":sys.argv[1],"enabled":True}))' "$url")"
    local result
    result="$(upsert_json_mcp "$OPENCODE_CONFIG" "upserted" "$name" "$payload" "mcp")"
    echo "  ✅ $name (OpenCode, $result)"
}

add_cursor_stdio() {
    local name="$1"
    local package="$2"
    local extra="$3"
    local payload
    payload="$(python3 -c 'import json,sys; print(json.dumps({"command":"npx","args":["-y",sys.argv[1],*sys.argv[2].split()]}))' "$package" "$extra")"
    local result
    result="$(upsert_json_mcp "$CURSOR_MCP" "upserted" "$name" "$payload" "mcpServers")"
    echo "  ✅ $name (Cursor, $result)"
}

add_cursor_http() {
    local name="$1"
    local url="$2"
    local payload
    payload="$(python3 -c 'import json,sys; print(json.dumps({"type":"http","url":sys.argv[1]}))' "$url")"
    local result
    result="$(upsert_json_mcp "$CURSOR_MCP" "upserted" "$name" "$payload" "mcpServers")"
    echo "  ✅ $name (Cursor, $result)"
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

echo "🔧 Setting up canonical MCP servers..."

echo ""
echo "📦 Installing NPM packages globally..."
install_npm_global "chrome-devtools-mcp"

echo ""
echo "🤖 Claude Code..."
add_claude_stdio chrome-devtools npx "${CHROME_DEVTOOLS_ARGS[@]}"
add_claude_http linear "$LINEAR_URL" linear-server
add_claude_http pylon "$PYLON_URL"
add_claude_http lightdash-docs "$LIGHTDASH_DOCS_URL"
strip_stale_claude_settings_mcp

echo ""
echo "🧠 Codex..."
add_codex_stdio chrome-devtools npx "${CHROME_DEVTOOLS_ARGS[@]}"
add_codex_http linear "$LINEAR_URL"
add_codex_http pylon "$PYLON_URL"
add_codex_http lightdash-docs "$LIGHTDASH_DOCS_URL"

echo ""
echo "⚡ OpenCode..."
add_opencode_stdio chrome-devtools "$CHROME_DEVTOOLS_PACKAGE" "--isolated"
add_opencode_http linear "$LINEAR_URL"
add_opencode_http pylon "$PYLON_URL"
add_opencode_http lightdash-docs "$LIGHTDASH_DOCS_URL"
remove_json_mcp "$OPENCODE_CONFIG" mcp graphite OpenCode

echo ""
echo "🖥️  Cursor..."
add_cursor_stdio chrome-devtools "$CHROME_DEVTOOLS_PACKAGE" "--isolated"
add_cursor_http pylon "$PYLON_URL"
add_cursor_http lightdash-docs "$LIGHTDASH_DOCS_URL"
echo "  ℹ️  Linear stays on the Cursor Linear plugin (not duplicated as MCP)"

echo ""
echo "📝 Restart Claude Code, Codex, OpenCode, and Cursor to load MCP servers."
echo ""
echo "🎉 MCP setup complete!"
