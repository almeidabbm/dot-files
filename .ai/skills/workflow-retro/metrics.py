#!/usr/bin/env python3
"""Weekly workflow metrics from local Claude Code, Codex, and Cursor transcripts.

Counts only sessions a person drove: worker, reviewer, scheduled, and approval
sessions are skipped. Prints JSON: one row per ISO week.

    python3 -I metrics.py [--weeks 10] [--plans <private plans folder>] > metrics.json
    python3 -I metrics.py --self-test
"""
import datetime as dt
import glob
import json
import os
import re
import sys
from collections import defaultdict

HOME = os.path.expanduser("~")
NOISE = ("<system-reminder", "<local-command", "<command-", "Caveat:", "<task-notification",
         "[Request interrupted", "<bash-", "# AGENTS.md", "<environment_context", "<user_instructions",
         "<INSTRUCTIONS", "<turn_aborted", "<skill", "<artifact-", "<ci-monitor-event", "<image",
         "</image", "# Files mentioned", "<send_user_message", "<hook_prompt", "<external_",
         "<in-app-browser", "<pasted_content")
WORKER = ("The following is the Codex agent history", ">>> ", "Reviewed Codex session", "Retained source", "Host notice",
          "Host:", "Role: independent", "Role:", "<scheduled-task", "This is an automated run",
          "Side conversation boundary")
PATTERNS = {
    "status_asks": r"where are we|what'?s happening|what are you doing|what'?s the (current )?state|where do we stand|how far|why is (this|it) taking",
    "size_pushback": r"so big|why so many|overcomplicat|too complex|scope creep|hacky|does it really need",
    "explain_asks": r"i don'?t (understand|get)|confus|in simple terms|tl;?dr|hard to (read|understand)|unreadable|too (long|verbose)|simplify",
    "handoff_asks": r"give me (a|the) (full )?(prompt|brief)|so i can (hand ?off|brief|give it)|another (session|agent)",
    "where_to_test": r"where can i (test|see|check|try)|is the (env|preview|environment).* up",
}
MERGE_RULE = re.compile(r"(merge|babysit)", re.I)


def clean(text):
    text = (text or "").strip()
    return None if not text or text.startswith(NOISE) else text


def parse_ts(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def read_jsonl(path):
    with open(path, errors="ignore") as handle:
        for line in handle:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def claude_sessions(cutoff):
    for path in glob.glob(f"{HOME}/.claude/projects/*/*.jsonl"):
        if os.path.getmtime(path) < cutoff or "-private-tmp-" in path:
            continue
        msgs = []
        for d in read_jsonl(path):
            if d.get("type") != "user" or d.get("isSidechain") or d.get("isMeta") or not d.get("timestamp"):
                continue
            content = d["message"].get("content")
            texts = [content] if isinstance(content, str) else [
                c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
            msgs += [(parse_ts(d["timestamp"]), t) for t in map(clean, texts) if t]
        yield "claude", msgs


def codex_sessions(cutoff):
    for path in glob.glob(f"{HOME}/.codex/sessions/*/*/*/*.jsonl"):
        if os.path.getmtime(path) < cutoff:
            continue
        msgs, worker = [], False
        for d in read_jsonl(path):
            p = d.get("payload") or {}
            if d.get("type") == "session_meta" and p.get("originator") == "codex_exec":
                worker = True
            if d.get("type") == "response_item" and p.get("type") == "message" and p.get("role") == "user":
                msgs += [(parse_ts(d["timestamp"]), t) for t in (clean(c.get("text")) for c in p.get("content", [])) if t]
        if not worker:
            yield "codex", msgs


def cursor_sessions(cutoff):
    # Cursor transcripts carry no per-line timestamps; the first query's <timestamp> tag, else file mtime.
    for path in glob.glob(f"{HOME}/.cursor/projects/*/agent-transcripts/*/*.jsonl"):
        if os.path.getmtime(path) < cutoff:
            continue
        when = dt.datetime.fromtimestamp(os.path.getmtime(path), dt.timezone.utc)
        msgs = []
        for d in read_jsonl(path):
            if d.get("role") != "user":
                continue
            for c in d.get("message", {}).get("content", []):
                text = c.get("text", "") if isinstance(c, dict) else ""
                m = re.search(r"<user_query>\s*(.*?)\s*</user_query>", text, re.S)
                if m and clean(m.group(1)):
                    msgs.append((when, m.group(1)))
        yield "cursor", msgs


def week_of(ts):
    iso = ts.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def plan_counts(plans):
    """Weekly sync packs written and pitches in them, by the week in each pack's file name."""
    counts = defaultdict(lambda: defaultdict(int))
    for path in glob.glob(os.path.join(plans, "weekly-sync", "*.md")):
        m = re.match(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
        if not m:
            continue
        week = week_of(dt.datetime.fromisoformat(m.group(1)))
        counts[week]["sync_packs"] += 1
        counts[week]["pitches"] += bool(re.search(r"^#+\s*Pitch", open(path).read(), re.M))
    return counts


def summarize(sessions, extra=None):
    seen, weeks = set(), defaultdict(lambda: defaultdict(float))
    hourly = defaultdict(set)  # (date, hour) -> session ids with a human message
    for sid, (tool, msgs) in enumerate(sessions):
        # Resumed and forked sessions copy earlier messages, sometimes re-stamped: dedupe per day.
        if not msgs or msgs[0][1].startswith(WORKER):
            continue
        fresh = [(ts, t) for ts, t in msgs if (ts.date(), t[:200]) not in seen]
        seen.update((ts.date(), t[:200]) for ts, t in msgs)
        if not fresh:
            continue
        fresh = [(ts, t) for ts, t in fresh if not t.startswith(WORKER)]
        start, end = fresh[0][0], fresh[-1][0]
        w = weeks[week_of(start)]
        w[f"sessions_{tool}"] += 1
        w["sessions"] += 1
        if (end - start).total_seconds() > 86400 and len(fresh) > 50:
            w["marathon_sessions"] += 1
        for ts, text in fresh:
            row = weeks[week_of(ts)]
            row["messages"] += 1
            for key, pattern in PATTERNS.items():
                if re.search(pattern, text, re.I):
                    row[key] += 1
            if MERGE_RULE.search(text) and len(text.split()) > 12:
                row["merge_rules_restated"] += 1
            if "continued from a previous conversation" in text:
                row["compactions"] += 1
            if tool != "cursor":
                hourly[(ts.date(), ts.hour)].add(sid)
    peaks = defaultdict(list)
    for (day, _), ids in hourly.items():
        peaks[week_of(dt.datetime.combine(day, dt.time()))].append(len(ids))
    for week, values in (extra or {}).items():
        weeks[week].update(values)
    current = week_of(dt.datetime.now(dt.timezone.utc))
    rows = []
    for week in sorted(weeks):
        row = {k: int(v) for k, v in weeks[week].items()}
        n = max(row.get("messages", 0), 1)
        row["week"] = week
        row["partial"] = week == current
        row["peak_parallel_sessions"] = max(peaks.get(week, [0]))
        for key in list(PATTERNS) + ["merge_rules_restated"]:
            row[f"{key}_per_100"] = round(100 * row.get(key, 0) / n, 1)
        rows.append(row)
    return rows


def self_test():
    t0 = dt.datetime(2026, 11, 2, 10, tzinfo=dt.timezone.utc)
    fake = [
        ("claude", [(t0, "where are we with this?"), (t0, "why is this so big")]),
        ("claude", [(t0, "where are we with this?"), (t0, "why is this so big")]),  # resumed copy
        ("codex", [(t0, "Role: independent reviewer")]),  # worker
        ("codex", [(t0, ">>> TRANSCRIPT START"), (t0, "where are we")]),  # approval reviewer
        ("codex", [(t0 + dt.timedelta(minutes=5), "babysit it and merge once build and test is green and no blockers remain")]),
    ]
    rows = summarize(fake)
    assert len(rows) == 1, rows
    r = rows[0]
    assert r["sessions"] == 2 and r["sessions_claude"] == 1 and r["sessions_codex"] == 1, r
    assert r["status_asks"] == 1 and r["size_pushback"] == 1 and r["merge_rules_restated"] == 1, r
    assert r["peak_parallel_sessions"] == 2, r
    print("self-test ok")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
        sys.exit()
    weeks = int(sys.argv[sys.argv.index("--weeks") + 1]) if "--weeks" in sys.argv else 10
    cutoff = (dt.datetime.now() - dt.timedelta(weeks=weeks)).timestamp()
    sessions = list(claude_sessions(cutoff)) + list(codex_sessions(cutoff)) + list(cursor_sessions(cutoff))
    sessions.sort(key=lambda s: s[1][0][0] if s[1] else dt.datetime.max.replace(tzinfo=dt.timezone.utc))
    plans = sys.argv[sys.argv.index("--plans") + 1] if "--plans" in sys.argv else None
    rows = summarize(sessions, plan_counts(plans) if plans else None)
    json.dump({"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
               "weeks": rows}, sys.stdout, indent=1)
