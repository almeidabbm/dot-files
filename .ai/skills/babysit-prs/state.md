# Babysitter state file

`~/work/state/babysit.json`. It exists so a pass can tell what moved, and so the
rerun budget survives a pass that dies half-way.

```json
{
  "version": 1,
  "updated": "2026-08-15T14:10:03Z",
  "prs": {
    "lightdash/lightdash#1234": {
      "head": "a1b2c3d4",
      "title": "Fix chart tooltips",
      "role": "author",
      "draft": false,
      "checks": {
        "CI / unit": {
          "conclusion": "failure",
          "verdict": "regression",
          "reported": "2026-08-15T14:10:03Z",
          "reruns": 0
        },
        "CI / e2e": {
          "conclusion": "success",
          "verdict": null,
          "reported": "2026-08-15T13:40:11Z",
          "reruns": 1
        }
      }
    }
  }
}
```

| Field | Read for | Written when |
| --- | --- | --- |
| `head` | Deciding a PR moved; reruns are budgeted per SHA | The head SHA changes — reset every check's `reruns` to 0 |
| `checks[].conclusion` | Deciding a check moved | Every pass that sees the check |
| `checks[].verdict` | Deciding a report is a transition | The verdict is decided |
| `checks[].reported` | Nothing — it is for the human reading the file | A Slack message names this check |
| `checks[].reruns` | The one-rerun-per-SHA cap | Immediately before `gh run rerun`, never after |

A PR that closes drops out of the file on the next pass. Keeping closed PRs
would grow the file without bound, and a closed PR's CI is nobody's problem.

Write the whole file atomically — render to `babysit.json.tmp` and `mv` it into
place — so a pass killed mid-write leaves the previous pass's state intact
rather than a truncated file the next pass cannot parse.
