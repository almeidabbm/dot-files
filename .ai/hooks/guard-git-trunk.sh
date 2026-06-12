#!/bin/bash

# PreToolUse(Bash) guard for AI coding agents.
#
# Enforces the one hard rule from shared-instructions.md that advisory text
# cannot guarantee: never commit to or push trunk (main/master/trunk) directly.
# Everything else — feature-branch commits, feature pushes, PR submits — is
# allowed.
#
# Protocol: reads the hook payload as JSON on stdin, extracts the Bash command,
# and exits 2 to BLOCK (the message on stderr is shown to the agent). Any other
# situation exits 0 to ALLOW. The guard fails open: if jq is missing or the
# payload is unreadable, it allows the command rather than bricking git.

input=$(cat)

# jq is required to parse the payload; without it, fail open.
command -v jq >/dev/null 2>&1 || exit 0

cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)
[[ -z "$cmd" ]] && exit 0

is_trunk() { [[ "$1" == "main" || "$1" == "master" || "$1" == "trunk" ]]; }

block() {
    echo "🚫 Blocked by dot-files git guard: $1" >&2
    echo "The shared workflow rules forbid touching trunk directly. Use a feature branch or a non-trunk target." >&2
    exit 2
}

# --- Guard: committing while on a trunk branch ---
if [[ "$cmd" == *"git commit"* ]]; then
    branch=$(git branch --show-current 2>/dev/null)
    is_trunk "$branch" && block "committing directly to '$branch'."
fi

# --- Guard: pushing to trunk ---
if [[ "$cmd" == *"git push"* ]]; then
    # A bare push from a trunk branch pushes trunk to its upstream.
    branch=$(git branch --show-current 2>/dev/null)
    is_trunk "$branch" && block "pushing from trunk branch '$branch'."

    # An explicit destination: inspect each token, resolving 'src:dst' refspecs
    # and a leading '+' (force). Exact-match only, so 'main-feature' is allowed.
    for tok in $cmd; do
        dst="${tok##*:}"
        dst="${dst#+}"
        is_trunk "$dst" && block "push targets trunk ('$tok')."
    done
fi

exit 0
