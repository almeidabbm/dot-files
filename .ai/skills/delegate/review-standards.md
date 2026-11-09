# Review standards

Corrections the user has made more than twice. A reviewer flags any violation as a should-fix, and a breaking change as a blocker. Add a rule here when the same correction comes up a third time.

- **Reuse first.** Use the existing component, icon, design token, copy pattern, endpoint style, or helper. A new UI pattern, hand-drawn icon, twin endpoint, or helper that duplicates an existing one needs a stated reason.
- **No machine-made styling.** No all-caps labels, eyebrow text, or decorative extras the surrounding UI does not use.
- **Only add or fix.** Behaviour with a feature flag off must match the default branch. Any change to existing behaviour is a blocker unless the spec asks for it.
- **Prove regressions.** Before calling something a regression, reproduce it on the default branch and say whether it is pre-existing or introduced.
- **Size against the estimate.** Compare the diff with the brief's estimate. Flag duplicated logic or tests, and anything outside the slice's scope.
- **No widened access.** New tokens, wildcard CORS, broader permissions, or new public surfaces need explicit user approval.
- **No generated files** in commits; CI generates them.
- **No customer names** in code, tests, fixtures, commits, or PR text.
