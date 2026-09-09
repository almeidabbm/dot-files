#!/bin/bash

# Render roles/*.md (single source) into each host's native agent format:
#   claude/<role>.md      Claude Code subagent (~/.claude/agents)
#   codex/<role>.toml     Codex custom agent   (~/.codex/agents)
#   opencode/<role>.md    OpenCode subagent    (~/.config/opencode/agents)
# The role name is the file name. Frontmatter fields: description, writes.
# Run after adding, editing, renaming, or removing a role. Output directories
# are rebuilt from scratch, and every output is parsed before it is accepted.
# Pass --check to verify the committed outputs are current without writing.

set -euo pipefail
shopt -s nullglob

DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$DIR"
CHECK=0
if [[ "${1:-}" == "--check" ]]; then
    CHECK=1
    OUT="$(mktemp -d)"
    trap 'rm -rf "$OUT"' EXIT
fi
for host in claude codex opencode; do
    rm -rf "${OUT:?}/$host"
    mkdir -p "$OUT/$host"
done

# Frontmatter is the block between the first two '---' fences; the body is everything after.
frontmatter() { awk '/^---$/ { c++; next } c == 1' "$1"; }
body() { awk '/^---$/ && c < 2 { c++; next } c == 2' "$1" | sed '1{/^$/d;}'; }
field() { frontmatter "$1" | sed -n "s/^$2: //p" | head -n 1; }

# Escape for a double-quoted YAML scalar or a TOML basic string (same rules for \ and ").
dq() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    printf '%s' "$s"
}

# Escape for a TOML multi-line basic string: backslashes, and any triple quote.
toml_ml() {
    local s="$1" q='"""' r='""\"'
    s="${s//\\/\\\\}"
    s="${s//$q/$r}"
    printf '%s' "$s"
}

roles=("$DIR"/roles/*.md)
if [[ ${#roles[@]} -eq 0 ]]; then
    echo "❌ no roles found in $DIR/roles" >&2
    exit 1
fi

for src in "${roles[@]}"; do
    role="$(basename "$src" .md)"
    desc="$(field "$src" description)"
    writes="$(field "$src" writes)"
    text="$(body "$src")"
    if [[ -z "$desc" ]]; then
        echo "❌ $src has no description" >&2
        exit 1
    fi

    {
        echo "---"
        echo "name: $role"
        echo "description: \"$(dq "$desc")\""
        [[ "$writes" == "true" ]] || echo "disallowedTools: Edit, Write, NotebookEdit"
        echo "---"
        echo
        echo "$text"
    } > "$OUT/claude/$role.md"

    {
        echo "name = \"$(dq "$role")\""
        echo "description = \"$(dq "$desc")\""
        if [[ "$writes" == "true" ]]; then
            echo 'sandbox_mode = "workspace-write"'
        else
            echo 'sandbox_mode = "read-only"'
        fi
        echo 'developer_instructions = """'
        echo "$(toml_ml "$text")"
        echo '"""'
    } > "$OUT/codex/$role.toml"

    {
        echo "---"
        echo "description: \"$(dq "$desc")\""
        echo "mode: subagent"
        if [[ "$writes" != "true" ]]; then
            echo "permission:"
            echo "  edit: deny"
        fi
        echo "---"
        echo
        echo "$text"
    } > "$OUT/opencode/$role.md"
done

# Every output must parse: TOML with tomllib, YAML frontmatter with PyYAML when installed.
python3 - "$OUT" <<'PY'
import glob, os, sys
out = sys.argv[1]
try:
    import tomllib
except ImportError:
    tomllib = None
try:
    import yaml
except ImportError:
    yaml = None
bad = 0
for path in glob.glob(os.path.join(out, "codex", "*.toml")):
    if tomllib is None:
        break
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        for key in ("name", "description", "sandbox_mode", "developer_instructions"):
            assert key in data, f"missing {key}"
    except Exception as e:
        print(f"❌ invalid TOML {path}: {e}", file=sys.stderr); bad += 1
for host in ("claude", "opencode"):
    for path in glob.glob(os.path.join(out, host, "*.md")):
        with open(path) as f:
            lines = f.read().split("\n")
        if lines[0] != "---" or "---" not in lines[1:]:
            print(f"❌ {path}: no frontmatter fences", file=sys.stderr); bad += 1; continue
        front = "\n".join(lines[1:lines.index("---", 1)])
        if yaml is not None:
            try:
                data = yaml.safe_load(front)
                assert isinstance(data, dict) and "description" in data
            except Exception as e:
                print(f"❌ invalid YAML frontmatter {path}: {e}", file=sys.stderr); bad += 1
sys.exit(1 if bad else 0)
PY

if [[ "$CHECK" -eq 1 ]]; then
    for host in claude codex opencode; do
        diff -r "$DIR/$host" "$OUT/$host" || { echo "❌ .ai/agents/$host is stale; run .ai/agents/render.sh"; exit 1; }
    done
    echo "✅ rendered agents are current and valid"
fi
