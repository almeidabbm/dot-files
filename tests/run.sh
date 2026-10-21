#!/bin/bash

# Behavioral tests for the link/unlink scripts.
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

echo "🧪 Nix configuration"
mkdir -p "$HOME/.config/nix"
printf 'keep\n' > "$HOME/.config/nix/local.conf"
"$DOTS/link-nix.sh" > "$TMP/link-nix.out"
check "nix: configuration directory is linked" '[[ -L "$HOME/.config/nix" && -f "$HOME/.config/nix/flake.lock" ]]'
check "nix: existing configuration is backed up" 'compgen -G "$HOME/.config/nix.backup.*/nix/local.conf" >/dev/null'
"$DOTS/link-nix.sh" >/dev/null
check "nix: repeated linking does not nest the link" '[[ "$(readlink "$HOME/.config/nix")" == "$DOTS/.config/nix" && ! -L "$DOTS/.config/nix/nix" ]]'
"$DOTS/unlink-nix.sh" >/dev/null
check "nix: unlink removes our configuration link" '[[ ! -e "$HOME/.config/nix" && ! -L "$HOME/.config/nix" ]]'
mkdir -p "$HOME/other-nix"
ln -s "$HOME/other-nix" "$HOME/.config/nix"
"$DOTS/unlink-nix.sh" >/dev/null
check "nix: unlink preserves another configuration link" '[[ -L "$HOME/.config/nix" ]]'
rm "$HOME/.config/nix"
mkdir -p "$HOME/.config/nix"
"$DOTS/unlink-nix.sh" >/dev/null
check "nix: unlink preserves a real configuration directory" '[[ -d "$HOME/.config/nix" && ! -L "$HOME/.config/nix" ]]'
"$DOTS/link-nix.sh" >/dev/null

echo ""
echo "🧪 link scripts"
# A machine linked before the worker agents were retired.
mkdir -p "$HOME/.claude/agents" "$HOME/.agents"
ln -s "$DOTS/.ai/agents/claude/reviewer.md" "$HOME/.claude/agents/reviewer.md"
ln -s "$DOTS/.ai/agents/roles" "$HOME/.agents/roles"
"$DOTS/link-claude.sh" >/dev/null && "$DOTS/link-codex.sh" >/dev/null && "$DOTS/link-opencode.sh" >/dev/null
check "claude: rules and skills linked" '[[ -L "$HOME/.claude/CLAUDE.md" && -e "$HOME/.claude/skills/git-workflow/SKILL.md" ]]'
check "codex: shared skills linked" '[[ -L "$HOME/.codex/AGENTS.md" && -e "$HOME/.agents/skills/delegate/SKILL.md" ]]'
check "retired agent and role links are pruned" '[[ ! -L "$HOME/.claude/agents/reviewer.md" && ! -L "$HOME/.agents/roles" ]]'

mkdir -p "$HOME/.codex/skills"
ln -s "$DOTS/.ai/skills/git-workflow" "$HOME/.codex/skills/git-workflow"
"$DOTS/link-codex.sh" >/dev/null
check "codex: legacy ~/.codex/skills link is migrated away" '[[ ! -e "$HOME/.codex/skills/git-workflow" && ! -L "$HOME/.codex/skills/git-workflow" ]]'

mv "$DOTS/.ai/skills/delegate" "$TMP/delegate"
"$DOTS/link-claude.sh" >/dev/null
check "claude: link whose source vanished is pruned" '[[ ! -L "$HOME/.claude/skills/delegate" ]]'
mv "$TMP/delegate" "$DOTS/.ai/skills/delegate"

EMPTY="$TMP/empty-dots"; mkdir -p "$EMPTY/.ai/skills"
rsync -a "$DOTS/" "$EMPTY/" && rm -rf "$EMPTY/.ai/skills"/*
sed "s|DOTFILES_DIR=\"\$HOME/Develop/dot-files\"|DOTFILES_DIR=\"$EMPTY\"|" "$EMPTY/link-claude.sh" > "$EMPTY/link-claude-empty.sh"
bash "$EMPTY/link-claude-empty.sh" >/dev/null
check "empty skills directory creates no '*' link" '[[ ! -L "$HOME/.claude/skills/*" ]]'
"$DOTS/link-claude.sh" >/dev/null

echo ""
echo "🧪 unlink scripts"
mkdir -p "$DOTS/.ai/skills-backup/keep"
ln -s "$DOTS/.ai/skills-backup/keep" "$HOME/.agents/skills/keep"
"$DOTS/unlink-codex.sh" >/dev/null
check "unlink-codex removes its own rules" '[[ ! -L "$HOME/.codex/AGENTS.md" ]]'
check "unlink-codex leaves shared ~/.agents skills" '[[ -e "$HOME/.agents/skills/delegate/SKILL.md" ]]'
check "unlink-codex leaves a link into a sibling directory (.ai/skills-backup)" '[[ -L "$HOME/.agents/skills/keep" ]]'
"$DOTS/unlink-claude.sh" >/dev/null
check "unlink-claude leaves shared ~/.agents skills" '[[ -e "$HOME/.agents/skills/delegate/SKILL.md" ]]'
"$DOTS/unlink.sh" >/dev/null 2>&1
check "unlink.sh removes shared ~/.agents skills" '[[ ! -L "$HOME/.agents/skills/delegate" ]]'
check "unlink.sh leaves the sibling-directory link alone" '[[ -L "$HOME/.agents/skills/keep" ]]'

echo ""
echo "────────────────────────────────"
echo "  $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]
