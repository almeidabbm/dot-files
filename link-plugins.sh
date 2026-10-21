#!/bin/bash

# Install the canonical user-level agent plugins for Claude Code, Codex, and OpenCode.
#
#   ponytail   DietrichGebert/ponytail   smallest complete change; /ponytail-review, /ponytail-audit
#
# Each host's plugin CLI owns the install and its updates; this script only declares the set.

set -uo pipefail

PONYTAIL_REPO="DietrichGebert/ponytail"
PONYTAIL_NPM="@dietrichgebert/ponytail"

run() {
    local label="$1"
    shift
    if "$@" >/dev/null 2>&1; then
        echo "  ✅ $label"
    else
        echo "  ⚠️  Failed: $label ($*)"
    fi
}

echo "🔌 Setting up agent plugins..."

echo ""
echo "🤖 Claude Code..."
if command -v claude >/dev/null; then
    if claude plugin marketplace list 2>/dev/null | grep -q "$PONYTAIL_REPO"; then
        echo "  ℹ️  ponytail marketplace already configured"
    else
        run "ponytail marketplace" claude plugin marketplace add "$PONYTAIL_REPO"
    fi
    run "ponytail plugin" claude plugin install ponytail@ponytail
else
    echo "  ℹ️  claude not installed, skipping"
fi

echo ""
echo "🧠 Codex..."
if command -v codex >/dev/null; then
    if codex plugin marketplace list 2>/dev/null | grep -q '^ponytail '; then
        echo "  ℹ️  ponytail marketplace already configured"
    else
        run "ponytail marketplace" codex plugin marketplace add "$PONYTAIL_REPO"
    fi
    run "ponytail plugin" codex plugin add ponytail@ponytail
    echo "  📝 Open /hooks in Codex once and trust ponytail's two lifecycle hooks"
else
    echo "  ℹ️  codex not installed, skipping"
fi

echo ""
echo "⚡ OpenCode..."
if command -v opencode >/dev/null; then
    run "ponytail plugin" opencode plugin add "$PONYTAIL_NPM"
else
    echo "  ℹ️  opencode not installed, skipping"
fi

echo ""
echo "📝 Restart Claude Code, Codex, and OpenCode to load plugins."
echo ""
echo "🎉 Plugin setup complete!"
