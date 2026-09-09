#!/bin/bash

# Render roles/*.md (single source) into each host's native agent format:
#   claude/<role>.md      Claude Code subagent (~/.claude/agents)
#   codex/<role>.toml     Codex custom agent   (~/.codex/agents)
#   opencode/<role>.md    OpenCode subagent    (~/.config/opencode/agents)
# Run after editing a role. Pass --check to verify outputs are current.

set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$DIR"
if [[ "${1:-}" == "--check" ]]; then
    OUT="$(mktemp -d)"
    trap 'rm -rf "$OUT"' EXIT
fi
mkdir -p "$OUT/claude" "$OUT/codex" "$OUT/opencode"

for src in "$DIR"/roles/*.md; do
    role="$(basename "$src" .md)"
    desc="$(sed -n 's/^description: //p' "$src")"
    writes="$(sed -n 's/^writes: //p' "$src")"
    body="$(awk '/^---$/ { c++; next } c >= 2' "$src" | sed '1{/^$/d;}')"

    {
        echo "---"
        echo "name: $role"
        echo "description: $desc"
        [[ "$writes" == "true" ]] || echo "disallowedTools: Edit, Write, NotebookEdit"
        echo "---"
        echo
        echo "$body"
    } > "$OUT/claude/$role.md"

    {
        echo "name = \"$role\""
        echo "description = \"$desc\""
        if [[ "$writes" == "true" ]]; then
            echo 'sandbox_mode = "workspace-write"'
        else
            echo 'sandbox_mode = "read-only"'
        fi
        echo 'developer_instructions = """'
        echo "$body"
        echo '"""'
    } > "$OUT/codex/$role.toml"

    {
        echo "---"
        echo "description: $desc"
        echo "mode: subagent"
        if [[ "$writes" != "true" ]]; then
            echo "permission:"
            echo "  edit: deny"
        fi
        echo "---"
        echo
        echo "$body"
    } > "$OUT/opencode/$role.md"
done

if [[ "${1:-}" == "--check" ]]; then
    for host in claude codex opencode; do
        diff -r "$DIR/$host" "$OUT/$host" || { echo "❌ .ai/agents/$host is stale; run .ai/agents/render.sh"; exit 1; }
    done
    echo "✅ rendered agents are current"
fi
