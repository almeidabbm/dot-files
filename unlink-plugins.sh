#!/bin/bash

# Remove the canonical agent plugins this repo installs. Marketplaces stay configured.

set -uo pipefail

run() {
    local label="$1"
    shift
    if "$@" >/dev/null 2>&1; then
        echo "  ✅ Removed $label"
    else
        echo "  ℹ️  $label not installed"
    fi
}

echo "🧹 Removing agent plugins..."

echo ""
command -v claude >/dev/null && run "ponytail from Claude Code" claude plugin uninstall --keep-data ponytail@ponytail
command -v codex >/dev/null && run "ponytail from Codex" codex plugin remove ponytail@ponytail
command -v opencode >/dev/null && run "ponytail from OpenCode" opencode plugin remove @dietrichgebert/ponytail

echo ""
echo "🎉 Plugin cleanup complete!"
