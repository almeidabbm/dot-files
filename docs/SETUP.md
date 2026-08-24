# Setup

Getting a machine from nothing to running agents on remote sandboxes.

Three parts, each usable on its own:

1. [The machine](#the-machine) — clone, link, verify
2. [Git and GitHub](#git-and-github) — identity, defaults, auth, keys
3. [Working in a stack](#working-in-a-stack) — the stacked-PR workflow

> Two links below — `.ai/HARNESS.md` and `.config/tmux/CHEATSHEET.md` — resolve once the
> documentation stack (PRs #26–#29) merges. Everything else is live on this branch.

---

## The machine

```bash
git clone git@github.com:almeidabbm/dot-files.git ~/Develop/dot-files
cd ~/Develop/dot-files
./link.sh          # symlinks everything into $HOME
./doctor.sh        # read-only check; non-zero on the first dangling link
```

`link.sh` projects `.ai/` into every agent tool's native location, so the workflow rules
and skills are identical in Claude Code, Codex, and OpenCode. See
[`.ai/HARNESS.md`](../.ai/HARNESS.md) for how that projection works and how to recover
when it breaks.

Dependencies worth having before you start:

```bash
brew install git gh jq tmux
gh extension install github/gh-stack
```

`jq` and `tmux` are not optional for this workflow: `jq` parses provider JSON, and `tmux`
is what keeps a remote agent alive after you disconnect.

`link.sh` puts the workflow CLI on your PATH via `~/.local/bin`:

```bash
agent-memory root      # workflow state
```

If your shell cannot find it, `~/.local/bin` is not on `PATH` — add it to `.zshrc`, or
run the installer directly with `./link-agent-memory.sh`.

---

## Git and GitHub

A fresh machine needs identity, defaults, an authenticated `gh`, an SSH key, and the
stacking extension. Work through this top to bottom.

### 1. Identity

```bash
git config --global user.name "Your Name"
git config --global user.email "you@personal.example"
```

The global identity is the fallback. Repositories cloned for work should carry the work
address instead, set per repository so a commit never lands under the wrong name:

```bash
cd ~/Develop/some-work-repo
git config user.email "you@company.example"
git config user.email   # verify before the first commit
```

Getting this wrong is expensive after the fact — the address is baked into every commit
object, and changing it means a rewrite. Check `git config user.email` in a new clone
before committing.

### 2. Global defaults

```bash
git config --global init.defaultBranch main
git config --global pull.rebase true
git config --global push.autoSetupRemote true
git config --global rerere.enabled true
git config --global fetch.prune true
git config --global diff.colorMoved zebra
```

| Setting | Value | Why |
| --- | --- | --- |
| `init.defaultBranch` | `main` | matches GitHub's default |
| `pull.rebase` | `true` | linear history, no merge commits from `git pull` |
| `push.autoSetupRemote` | `true` | `git push` works on a new branch without `-u` |
| `rerere.enabled` | `true` | replays a conflict resolution you already made — the same conflict recurs on every branch above it in a stack |
| `fetch.prune` | `true` | drops remote-tracking refs for deleted branches |
| `diff.colorMoved` | `zebra` | colours moved code differently from added code |

`rerere` earns its place the moment you work in stacks: a cascading rebase replays the
same conflict once per layer, and rerere resolves the repeats from the resolution you
gave the first time. `gh stack init` turns it on for you, but setting it globally means
it also covers plain rebases.

### 3. GitHub CLI

```bash
brew install gh
gh auth login      # choose GitHub.com, HTTPS or SSH, authenticate in browser
gh auth status     # verify: account, protocol, token scopes
```

`gh auth status` is the check that matters — it prints the active account, the git
protocol `gh` will use, and the token scopes. If a later `gh` command fails on
permissions, re-run it here first.

### 4. SSH keys

```bash
ssh-keygen -t ed25519 -C "you@personal.example"
eval "$(ssh-agent -s)"
ssh-add --apple-use-keychain ~/.ssh/id_ed25519    # macOS; use `ssh-add` elsewhere
```

Upload the public half through `gh` rather than the web UI, then test:

```bash
gh ssh-key add ~/.ssh/id_ed25519.pub --title "$(hostname -s)"
ssh -T git@github.com
```

A successful test greets you by username and exits non-zero — that is expected, GitHub
does not grant a shell.

On macOS, persist the key across reboots by adding to `~/.ssh/config`:

```
Host github.com
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
```

### 5. The `gh stack` extension

Stacked pull requests are native to GitHub, delivered as a `gh` extension:

```bash
gh extension install github/gh-stack
gh extension list | grep -q gh-stack && echo "installed"
gh stack --version
```

The shared workflow rules in `.ai/shared-instructions.md` assume this extension is
present. They cover commits (Conventional Commits, no `Co-Authored-By` trailers),
worktrees under `.worktrees/`, and stacking — but deliberately state **no branch
policy**. Each repository owns that, through its own `AGENTS.md`/`CLAUDE.md`, branch
protection, or CI. Follow what the repository states rather than assuming a rule it has
not written down.

---

## Working in a stack

A stack is a chain of branches where each one is based on the one below it, and each
becomes its own pull request. The bottom branch targets trunk; every other branch targets
its parent. Small, reviewable PRs without waiting for the one below to merge.

### Starting a stack

From trunk, for new work:

```bash
gh stack init my-feature                     # one branch on the default branch
gh stack init auth-layer api-routes ui       # a multi-layer stack in one command
gh stack init --base develop my-feature      # a non-default trunk
```

`gh stack init` adopts branches that already exist and creates the ones that do not, so
the same command turns loose branches into a stack. Pass them **bottom to top** — the
first argument sits on trunk, each subsequent one on its predecessor:

```bash
gh stack init feat/auth feat/api feat/ui
```

### Adding layers and moving around

```bash
gh stack add my-next-layer                   # new branch on top of the current stack
gh stack add -Am "feat: add token refresh" auth-refresh   # stage all, commit, branch
gh stack add -m "fix: correct login redirect"             # branch name from the message
```

| Command | What it does |
| --- | --- |
| `gh stack view` | the stack with PR status per branch |
| `gh stack view --short` | one line per branch |
| `gh stack switch` | interactive picker across the stack |
| `gh stack up` / `gh stack down` | one layer further from / closer to trunk |
| `gh stack top` / `gh stack bottom` | the extremes |
| `gh stack trunk` | back to the trunk branch |
| `gh stack checkout <n\|pr-url\|branch>` | check out a stack, fetching it if it is only on GitHub |

### Submitting

```bash
gh stack submit           # interactive editor: pick branches, write titles, submit
gh stack submit --auto    # skip the editor, auto-generated titles
gh stack submit --open    # mark new and existing PRs ready for review
```

Draft state depends on how you submit. In the interactive editor new PRs default to ready
for review, with a "CREATE AS" toggle per PR. Non-interactively — `--auto`, or any
non-TTY such as an agent session or CI — **new PRs are created as drafts** unless you pass
`--open`. If you submit from a script and the PRs come out as drafts, that is why.

`submit` pushes every branch, creates or updates the PRs, fixes up base branches, and
links them into a stack on GitHub.

### Staying in sync

```bash
gh stack sync            # fetch, cascade-rebase, push atomically, sync PR state
gh stack sync --prune    # also delete local branches for merged PRs
```

`sync` never opens pull requests; it only links ones that already exist. If it detects a
rebase conflict it restores every branch to its original state and tells you to run
`gh stack rebase` to resolve interactively.

For rebasing alone:

```bash
gh stack rebase              # the whole stack
gh stack rebase --downstack  # trunk up to the current branch
gh stack rebase --upstack    # the current branch up to the top
gh stack rebase --no-trunk   # inter-branch only, no fetch or trunk rebase
```

### Amending a branch mid-stack

`gh stack modify` is the interactive **restructure** UI — drop, fold, reorder, rename. It
is not an amend, and it requires a clean working tree, linear history, and no rebase in
progress.

To change a commit on a branch partway up the stack:

```bash
git commit --amend
gh stack rebase --upstack
```

The amend rewrites the current branch; `--upstack` carries the new tip into every layer
above it. Without the rebase, the branches above still point at the old commit.

### When a rebase conflicts

Stop. Show the conflicts and let a human decide:

```bash
git status                       # conflicted paths
gh stack rebase --continue       # after resolving
gh stack rebase --abort          # restore every branch
```

Do not guess through a stack conflict. The same resolution replays up the stack via
`rerere`, so a wrong call propagates through every layer above it.

### Fallbacks when stacking is unavailable

Stacking is enabled per repository. A `gh stack` command that exits with code `9` means
stacked pull requests are not turned on for that repository.

| Stacked | Fallback |
| --- | --- |
| `gh stack init <branch>` | `git checkout -b <branch>` |
| `gh stack view` | `git log --oneline --graph --decorate --all -20` |
| `gh stack submit` | `gh pr create --base <parent-branch>`, once per branch, in stack order |
| `gh stack sync` / `rebase` | `git fetch origin`, then rebase each child branch by hand |
| amend + `rebase --upstack` | `git commit --amend`, then rebase each downstream branch by hand |

Say so explicitly when you fall back: downstream branches will **not** be rebased
automatically, and the PRs will **not** appear as a linked stack on GitHub. Both are
manual from then on.

### Worked example: four branches adopted into one stack

This repository's documentation work landed exactly this way. Four branches already
existed with their commits; they were adopted bottom to top and submitted in one pass:

```bash
git checkout main && git pull --rebase

gh stack init \
  docs/harness-guide \
  chore/drop-trunk-guard \
  docs/simplify-readme \
  feat/tmux-config

gh stack view --short
gh stack submit --open
```

The resulting chain, each PR based on the one below it:

| PR | Branch | Base |
| --- | --- | --- |
| #29 | `feat/tmux-config` | `docs/simplify-readme` |
| #28 | `docs/simplify-readme` | `chore/drop-trunk-guard` |
| #27 | `chore/drop-trunk-guard` | `docs/harness-guide` |
| #26 | `docs/harness-guide` | `main` |

Reviewers see four small PRs instead of one sprawling diff, and GitHub shows the stack on
each. When #26 merges, `gh stack sync --prune` rebases the rest onto the new trunk, drops
the merged local branch, and repoints #27 at `main`.
