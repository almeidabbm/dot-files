# Setup

Getting a machine from nothing to running agents on remote sandboxes.

Four parts, each usable on its own:

1. [The machine](#the-machine) — clone, link, verify
2. [Git and GitHub](#git-and-github) — identity, defaults, auth, keys
3. [Working in a stack](#working-in-a-stack) — the stacked-PR workflow
4. [Remote agents](#remote-agents) — exe.dev setup and running agents against our repos

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

`link.sh` puts both CLIs on your PATH via `~/.local/bin`:

```bash
agent-memory root      # workflow state
agent-run status       # remote sandboxes
```

If your shell cannot find them, `~/.local/bin` is not on `PATH` — add it to `.zshrc`, or
run the installers directly with `./link-agent-memory.sh` and `./link-agent-run.sh`.
`agent-run` additionally needs the `jsonschema` and `pyyaml` Python modules; its installer
warns if either is missing.

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

---

## Remote agents

`agent-run` puts a coding agent on a disposable exe.dev VM, one VM per task, and gives
you a way to watch it. Full command reference in
[`agent-run/README.md`](../agent-run/README.md); this section is the setup and the two
worked examples against our own repositories.

### 1. exe.dev account setup

Done once, and parts of it must be interactive — integration management is blocked over
non-interactive SSH.

```bash
ssh exe.dev whoami       # confirms your key is registered
ssh exe.dev ls --json    # lists your VMs; {"vms":[]} is a clean slate
ssh exe.dev int list     # lists integrations
```

You want integrations of two kinds:

| Kind | Gives you | Attach as |
| --- | --- | --- |
| `llm` | Model access with no credential on the VM | `auto:all` |
| `github` | Cloning private repos with no token on the VM | `auto:all` while the key is tag-scoped |

**Attachment matters more than it looks.** An exe.dev SSH key is scoped to a single tag,
and yours is scoped to a tag named after the key type:

```console
$ ssh exe.dev new --tag=my-tag ...
{"error":"--tag SSH key scoped to tag \"ssh-ed25519\" can only use --tag=ssh-ed25519"}
```

Every VM the key creates is auto-tagged `ssh-ed25519`, and no other tag can be set — so an
integration attached to any *other* tag can never reach your VMs. Nor is per-VM attachment
available:

```console
$ ssh exe.dev new --integration=lightdash-lightdash ...
{"error":"tag-scoped SSH keys cannot modify integrations"}
```

So while the key is tag-scoped, **every** integration has to be attached on the account —
`auto:all`, or `tag:ssh-ed25519` which every VM already carries — and templates must leave
`integrations:` and `tags:` empty.

That is a real cost: attaching a repo integration account-wide means every VM can reach
that repo, and with `act-as-user` a push is attributed to your GitHub account. Per-VM
scoping comes back with an unscoped key:

```bash
ssh-keygen -t ed25519 -C "exe-dev" -f ~/.ssh/id_exe
cat ~/.ssh/id_exe.pub | ssh exe.dev ssh-key add     # no --tag = unscoped
```

Pipe the key rather than passing it as an argument. `ssh-key add [--tag=TAG] <public-key>`
takes a tag flag, and because the gateway strips shell quoting, a quoted public key passed
inline arrives split — which is how a key ends up scoped to a tag named `ssh-ed25519`, the
first token of the key itself.

**Do not assume the integration named `llm` is the right one.** An account can hold
several: one may serve OpenAI from a personal ChatGPT subscription while another serves
Anthropic from the managed gateway. `exeuntu configure <agent>` always targets the one
literally named `llm`, so it picks the wrong source the moment providers are split — and
the resulting failure looks like a broken runtime rather than a misrouted request.
`agent-run`'s `configure-llm-integration` step instead asks
`reflection.int.exe.xyz/integrations` what is attached, asks each candidate which models
it serves, uses the one matching the runtime, and exits non-zero when none does.

The `llm` integration is what makes headless runs possible. Both Codex and Claude Code
reach the model through `llm.int.exe.xyz`, with the credential injected at the network
layer — the VM can use it but never read it, and no `codex login` or `claude` login is
needed. `exeuntu configure <agent>` on the VM wires this up, and `agent-run` runs it for
you via the `configure-llm-integration` setup step.

For the `github` integration, prefer read-only until a task genuinely needs to push:

```text
int add github --name=github --repository=lightdash/lightdash --readonly
```

#### Reaching the web UI

Some setup is browser-only, and the shortcut for getting there may not work for you:

```console
$ ssh exe.dev browser
command not allowed by SSH key permissions
```

`browser` generates a magic link to the website, and an exe.dev SSH key carries a `cmds`
allowlist that can exclude it. That blocks the shortcut, not the destination — sign in
directly at **<https://exe.dev>** with "Login / Register" using the email from
`ssh exe.dev whoami`.

Run `ssh exe.dev help` to see which commands your key does allow; `ssh exe.dev doc
https-api` documents the permission model, where `cmds` lists the permitted commands.

The same allowlist is why your key is **tag-scoped** and rejects custom `--tag` values —
`agent-run` puts run metadata in `--comment` instead.

#### Connecting a ChatGPT subscription

Only needed if you want the OpenAI provider to use your personal ChatGPT plan rather than
exe.dev's managed gateway. Per exe.dev's own docs this is browser-only, and it is
available **only on a personal LLM integration** — a team integration can use the gateway
or an API key, not a subscription.

1. Enable device-code login in ChatGPT's security settings (personal account) or
   workspace permissions (workspace admin).
2. At <https://exe.dev>, open **Integrations → LLM**.
3. Connect the ChatGPT account, then select it as the OpenAI source.

#### Connecting GitHub

Also from **Integrations** in the browser: link your GitHub account, which installs the
exe.dev GitHub App into your account or organisation. Only after that can you create
per-repo integrations, which you can do over SSH:

```text
int add github --name=github --repository=lightdash/lightdash --readonly
```

### 2. Our repos

Two templates ship, and they differ in exactly the way that matters — whether the repo is
public.

| Template | Repo | Needs `github` integration? | Ready in |
| --- | --- | --- | --- |
| `dot-files.yaml` | `almeidabbm/dot-files` (public) | no — clones anonymously | ~1 min |
| `lightdash-dev.yaml` | `lightdash/lightdash` (private) | **yes** | several min (`pnpm install`) |

Start with `dot-files`. It is the smallest end-to-end path, so if something is wrong with
your account, key, or integrations, it fails fast and cheaply.

### 3. A run, start to finish

```bash
cd ~/Develop/dot-files

# 1. dispatch: create the VM, clone, configure the runtime, wait for readiness
agent-run dispatch agent-run/templates/dot-files.yaml \
  --runtime codex --name my-task

# 2. run: start the agent inside tmux on the VM, from a prompt file
agent-run run my-task --prompt-file ./TASK.md

# 3. watch
agent-run status                     # every run: VM state and agent state
agent-run stat my-task               # progress, tokens, cpu/memory/disk
agent-run logs my-task --follow      # stream this one
agent-run attach my-task             # take the wheel; Ctrl-b d to leave it running

# 4. stop the agent but keep the VM and its output
agent-run stop my-task

# 5. clean up — always
agent-run rm my-task
ssh exe.dev ls --json                # confirm: {"vms":[]}
```

Swap `--runtime codex` for `--runtime claude` and nothing else changes. Both runtimes have
been verified end to end on the identical task.

For lightdash, allow for the monorepo install:

```bash
agent-run dispatch agent-run/templates/lightdash-dev.yaml \
  --runtime codex --name ld-bug --wait-timeout 1800
```

### 3a. Driving one by hand

Not every session is a fire-and-forget task. To sit at the runtime yourself:

```bash
agent-run run my-task --interactive --sandbox danger-full-access
agent-run attach my-task          # Ctrl-b d leaves it running
```

Or skip the agent entirely and get a shell on the VM:

```bash
agent-run shell my-task
```

Both connect straight to the VM rather than through the exe.dev gateway, because the
gateway allocates no TTY — `ssh -tt exe.dev ssh <vm> tty` reports `not a tty`, which is
why tmux fails with "open terminal failed" if you route an interactive session through it.

### 4. Watching several at once

```bash
agent-run monitor                # one tmux window per live run
tmux attach -t agent-run         # Ctrl-b n / p to move, Ctrl-b d to leave
```

Re-running `monitor` opens windows for new runs and prunes finished ones without
disturbing the window you are watching. New to tmux? See
[`.config/tmux/CHEATSHEET.md`](../.config/tmux/CHEATSHEET.md).

### 5. Writing the task prompt

The prompt is the whole input, so make the finish line checkable. What has worked:

- Name the repository path and the branch to create.
- Ask for a specific, small change — one file where possible.
- **Require evidence, not prose**: the exact test command and its exit status from
  `echo $?`, plus `git status --short` and `git diff --stat`.
- Give it an honest escape hatch: "if the thing I described does not exist, report what
  you actually found rather than inventing it."
- Say what not to touch: do not push, do not open a PR, do not modify other files.

Then verify independently rather than trusting the report — re-run the tests yourself over
SSH, read the diff, and where the change is a test, mutate the code it covers and confirm
the test fails. An agent's claim that tests passed is not evidence; the command and its
exit status are.

### 6. Choosing a sandbox

The one call to make consciously. `--sandbox workspace-write` (the default) is least
privilege, but it makes `.git` read-only, so **the agent cannot create a branch or
commit**. `--sandbox danger-full-access` allows git and leaves the VM as the only
isolation boundary — which is reasonable for a disposable single-task VM holding a public
repo and no credentials, and less so otherwise.

The trade-off table lives in [`agent-run/README.md`](../agent-run/README.md#choosing-a-sandbox).

### 7. Security rules that hold everywhere

- No provider API key ever reaches a VM. `agent-run` rejects `OPENAI_API_KEY` and
  `ANTHROPIC_API_KEY` in template `env`, and a test asserts no shipped template carries a
  credential-shaped value.
- Model and repo access ride the integration gateways, so credentials stay off the VM.
- Template `env` is plaintext on the VM: non-secret configuration only.
- Central task memory stays local. Send a task-scoped prompt, never the memory root.
- Delete the VM when the evidence is captured, and confirm with `ssh exe.dev ls --json`.

### 8. When it misbehaves

| Symptom | Cause | Fix |
| --- | --- | --- |
| `VM name "x" is not available` | A record exists locally, or the name is taken | Pick another `--name`, or `agent-run rm x` |
| Dispatch never reaches ready | A readiness check is failing | `agent-run logs <name> --source setup` |
| `error: unexpected argument` from a runtime | The gateway stripped shell quoting | Put the command in a script and push it; `agent-run` does this already |
| Agent cannot create a branch | `workspace-write` makes `.git` read-only | `--sandbox danger-full-access` |
| `monitor` says tmux is missing | No local tmux | `brew install tmux`, or use `logs --follow` and `attach`, which need none |
| Clone fails on a private repo | No `github` integration | Link GitHub at <https://exe.dev> → Integrations, then `int add github …` |
