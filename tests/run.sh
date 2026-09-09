#!/bin/bash

# Behavioral tests for the agent renderer and the link/unlink scripts.
# Runs everything against a temporary HOME with this repo copied to
# $HOME/Develop/dot-files, so the scripts' hardcoded paths resolve there
# and the real home directory is never touched.

set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export HOME="$TMP"
DOTS="$HOME/Develop/dot-files"
mkdir -p "$DOTS"
rsync -a --exclude .git "$REPO/" "$DOTS/"

pass=0
fail=0
ok()   { echo "  ✅ $1"; ((pass++)); }
bad()  { echo "  ❌ $1"; ((fail++)); }
check() { if eval "$2"; then ok "$1"; else bad "$1"; fi; }

echo "🧪 renderer"
ROLES="$DOTS/.ai/agents/roles"
cat > "$ROLES/edge.md" <<'ROLE'
---
description: Says "hi": a colon, a backslash \ and 'quotes'.
writes: true
---

Line one.

---

Fields a brief may contain at column zero:

description: not the frontmatter description
writes: false

A TOML hazard: """ and C:\temp\x.
ROLE
"$DOTS/.ai/agents/render.sh" >/dev/null 2>"$TMP/render.err"
check "render succeeds on the edge role" '[[ $? -eq 0 ]] && [[ -f "$DOTS/.ai/agents/codex/edge.toml" ]]'
python3 - "$DOTS/.ai/agents" > "$TMP/py.out" 2>&1 <<'PY'
import sys, tomllib
out = sys.argv[1]
t = tomllib.load(open(f"{out}/codex/edge.toml", "rb"))
assert t["description"] == 'Says "hi": a colon, a backslash \\ and \'quotes\'.', t["description"]
assert t["sandbox_mode"] == "workspace-write", t["sandbox_mode"]
body = t["developer_instructions"]
assert "\n---\n" in body, "horizontal rule lost"
assert '"""' in body and "C:\\temp\\x" in body, body
for host in ("claude", "opencode"):
    text = open(f"{out}/{host}/edge.md").read()
    front, rest = text.split("\n---\n", 1)[0], text.split("\n---\n", 1)[1]
    assert 'description: "Says \\"hi\\": a colon, a backslash \\\\ and \'quotes\'."' in front, front
    assert "\n---\n" in rest, f"{host}: horizontal rule lost"
    assert "disallowedTools" not in front and "edit: deny" not in front, f"{host}: writes lost"
try:
    import yaml
    for host in ("claude", "opencode"):
        text = open(f"{out}/{host}/edge.md").read()
        data = yaml.safe_load(text.split("\n---\n", 1)[0].split("---\n", 1)[1])
        assert data["description"].startswith('Says "hi"'), data
except ImportError:
    pass
print("ok")
PY
check "edge role renders valid, escaped, unclipped output" '[[ "$(cat "$TMP/py.out")" == "ok" ]]'
rm "$ROLES/edge.md"
"$DOTS/.ai/agents/render.sh" >/dev/null 2>&1
check "removing a role removes its rendered outputs" '[[ ! -e "$DOTS/.ai/agents/codex/edge.toml" && ! -e "$DOTS/.ai/agents/claude/edge.md" && ! -e "$DOTS/.ai/agents/opencode/edge.md" ]]'
check "--check passes after a render" '"$DOTS/.ai/agents/render.sh" --check >/dev/null 2>&1'
echo "- extra line" >> "$ROLES/reviewer.md"
check "--check fails when a role changed after the last render" '! "$DOTS/.ai/agents/render.sh" --check >/dev/null 2>&1'
"$DOTS/.ai/agents/render.sh" >/dev/null 2>&1

echo ""
echo "🧪 link scripts"
"$DOTS/link-claude.sh" >/dev/null && "$DOTS/link-codex.sh" >/dev/null && "$DOTS/link-opencode.sh" >/dev/null
check "claude: rules, skills, agents linked" '[[ -L "$HOME/.claude/CLAUDE.md" && -e "$HOME/.claude/skills/git-workflow/SKILL.md" && -e "$HOME/.claude/agents/reviewer.md" ]]'
check "codex: agents and shared skills linked" '[[ -e "$HOME/.codex/agents/reviewer.toml" && -e "$HOME/.agents/skills/delegation/SKILL.md" && -e "$HOME/.agents/roles/reviewer.md" ]]'
check "opencode: agents linked" '[[ -e "$HOME/.config/opencode/agents/reviewer.md" ]]'

mkdir -p "$HOME/.codex/skills"
ln -s "$DOTS/.ai/skills/git-workflow" "$HOME/.codex/skills/git-workflow"
"$DOTS/link-codex.sh" >/dev/null
check "codex: legacy ~/.codex/skills link is migrated away" '[[ ! -e "$HOME/.codex/skills/git-workflow" && ! -L "$HOME/.codex/skills/git-workflow" ]]'

mv "$DOTS/.ai/agents/claude/investigator.md" "$TMP/investigator.md"
"$DOTS/link-claude.sh" >/dev/null
check "claude: link whose source vanished is pruned" '[[ ! -L "$HOME/.claude/agents/investigator.md" ]]'
mv "$TMP/investigator.md" "$DOTS/.ai/agents/claude/investigator.md"

EMPTY="$TMP/empty-dots"; mkdir -p "$EMPTY/.ai/skills" "$EMPTY/.ai/agents/claude"
rsync -a "$DOTS/" "$EMPTY/" && rm -rf "$EMPTY/.ai/skills"/* "$EMPTY/.ai/agents/claude"/*
sed "s|DOTFILES_DIR=\"\$HOME/Develop/dot-files\"|DOTFILES_DIR=\"$EMPTY\"|" "$EMPTY/link-claude.sh" > "$EMPTY/link-claude-empty.sh"
bash "$EMPTY/link-claude-empty.sh" >/dev/null
check "empty skills/agents directories create no '*' link" '[[ ! -L "$HOME/.claude/skills/*" && ! -L "$HOME/.claude/agents/*" ]]'
"$DOTS/link-claude.sh" >/dev/null

echo ""
echo "🧪 unlink scripts"
mkdir -p "$DOTS/.ai/skills-backup/keep"
ln -s "$DOTS/.ai/skills-backup/keep" "$HOME/.agents/skills/keep"
"$DOTS/unlink-codex.sh" >/dev/null
check "unlink-codex removes its own agents" '[[ ! -L "$HOME/.codex/agents/reviewer.toml" && ! -L "$HOME/.codex/AGENTS.md" ]]'
check "unlink-codex leaves shared ~/.agents skills and roles" '[[ -e "$HOME/.agents/skills/delegation/SKILL.md" && -e "$HOME/.agents/roles/reviewer.md" ]]'
check "unlink-codex leaves a link into a sibling directory (.ai/skills-backup)" '[[ -L "$HOME/.agents/skills/keep" ]]'
"$DOTS/unlink-claude.sh" >/dev/null
check "unlink-claude leaves shared ~/.agents roles" '[[ -e "$HOME/.agents/roles/reviewer.md" ]]'
"$DOTS/unlink.sh" >/dev/null 2>&1
check "unlink.sh removes shared ~/.agents skills and roles" '[[ ! -L "$HOME/.agents/skills/delegation" && ! -L "$HOME/.agents/roles" ]]'
check "unlink.sh leaves the sibling-directory link alone" '[[ -L "$HOME/.agents/skills/keep" ]]'

echo ""
echo "────────────────────────────────"
echo "  $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]
