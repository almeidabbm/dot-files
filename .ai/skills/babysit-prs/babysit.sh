#!/usr/bin/env bash
# Supervisor for the PR babysitter.
#
# The loop lives here rather than inside the agent: `claude -p` is one bounded
# pass, so a pass that crashes, hangs, or exhausts its context costs one
# interval instead of the whole watch. Each pass starts with fresh context and
# reads its memory from the state file.
#
#   babysit.sh once   - run a single pass in the foreground
#   babysit.sh loop   - run passes forever, one every $BABYSIT_INTERVAL seconds

set -uo pipefail

WORK="${WORK:-$HOME/work}"
SKILL="$WORK/dot-files/.ai/skills/babysit-prs"
STATE_DIR="$WORK/state"
LOG="$WORK/babysit.log"
LOCK="$STATE_DIR/babysit.lock"
INTERVAL="${BABYSIT_INTERVAL:-600}"

# A pass on a busy watch set can outrun a short interval. flock makes the
# overlap a skipped pass instead of two agents writing one state file.
PASS_TIMEOUT="${BABYSIT_PASS_TIMEOUT:-900}"

mkdir -p "$STATE_DIR"

log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >>"$LOG"; }

# One pass, already holding the lock. Reached only by re-invoking this script,
# so the lock wraps a real process rather than an exported shell function.
run_pass() {
    log "pass: start"
    # git pull keeps the brain current: editing SKILL.md and pushing is enough
    # to change the babysitter's behaviour, with no redispatch.
    git -C "$WORK/dot-files" pull --quiet --ff-only 2>>"$LOG" \
        || log "pass: git pull failed, using the checkout as-is"

    timeout "$PASS_TIMEOUT" claude -p \
        "Run one PR-health pass. Follow $SKILL/SKILL.md exactly, including its guardrails." \
        --permission-mode bypassPermissions \
        >>"$LOG" 2>&1
    local rc=$?

    case "$rc" in
        0)   log "pass: ok" ;;
        124) log "pass: timed out after ${PASS_TIMEOUT}s" ;;
        *)   log "pass: exit $rc" ;;
    esac
}

locked_pass() {
    flock -n 9 || { log "pass: skipped, another pass holds the lock"; return 0; }
    run_pass
} 9>"$LOCK"

case "${1:-loop}" in
    once)
        locked_pass
        ;;
    loop)
        log "supervisor: start (interval ${INTERVAL}s)"
        # Setup starts this session before the readiness checks run, so hold the
        # first pass until the box is declared ready rather than racing gh's
        # own install.
        for _ in $(seq 1 60); do
            [ -f "$WORK/.agent-run-ready" ] && break
            sleep 5
        done
        while true; do
            locked_pass
            sleep "$INTERVAL"
        done
        ;;
    *)
        echo "usage: babysit.sh [once|loop]" >&2
        exit 2
        ;;
esac
