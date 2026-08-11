# agent-run

Code-driven, provider-agnostic sandbox templates for remote coding agents.

A **template** (`templates/*.yaml`, validated by `templates/schema.json`)
describes what an environment needs — resources, repositories, allowed
runtimes, env, setup steps, readiness checks — without saying anything about
how a given provider builds it. A **provider adapter** compiles the template
into concrete lifecycle calls. The coding-agent runtime (Codex or Claude Code)
is a dispatch-time flag, not a template fork.

`validate` and `compile` never touch a provider — compile prints the creation
command for you to review. `dispatch` is the automated path: it compiles,
creates the VM, waits for readiness, and records the run locally; `status` and
`rm` manage dispatched runs.

## Usage

```sh
agent-run/bin/agent-run validate agent-run/templates/lightdash-dev.yaml

# manual path: review the command, run it yourself
agent-run/bin/agent-run compile agent-run/templates/lightdash-dev.yaml \
  --runtime codex
# setup script -> lightdash-dev-codex-setup.sh (447 bytes)
# ssh exe.dev new --json --name=lightdash-dev-codex --cpu=4 ... < lightdash-dev-codex-setup.sh

# automated path: one command per task, safe to run in parallel
agent-run/bin/agent-run dispatch agent-run/templates/lightdash-dev.yaml \
  --runtime codex --name task-a --prompt-file task-a.md
agent-run/bin/agent-run dispatch agent-run/templates/lightdash-dev.yaml \
  --runtime codex --name task-b --prompt-file task-b.md

agent-run/bin/agent-run status        # run states, cross-checked against the provider
agent-run/bin/agent-run logs task-a   # tail the VM's first-boot setup log
agent-run/bin/agent-run rm task-a     # delete the VM (asks first; --yes to skip)
```

`dispatch` creates the VM, polls for the readiness marker, copies the prompt
file to `~/work/TASK.md`, then prints the interactive steps that remain yours
by design: subscription login and Happy pairing on that VM. Run records live
under `~/.local/state/agent-run/` (override with `AGENT_RUN_STATE_PATH`);
they are machine-local state, not repo content.

Requires `python3` with `pyyaml` and `jsonschema`.

## Template contract

```yaml
version: 1
name: lightdash-dev            # also the default VM name prefix
resources: { cpu: 4, memory: 8GB, disk: 50GB }
runtimes: [codex, claude]      # allowed; picked with --runtime at compile time
repos:
  - id: github.com/lightdash/lightdash   # host/owner/repo
    ref: main
    path: lightdash            # checkout dir under $HOME/work
    role: primary
env:
  NODE_ENV: development        # provider API keys are rejected by design
setup:
  - update-runtimes            # named step: updates only the selected runtime
  - install-happy              # named step: npm install -g happy
  - run: corepack enable && pnpm install
    cwd: lightdash
checks:                        # must exit 0 before the readiness marker
  - node --version
providers:                     # the only place provider specifics may appear
  exe.dev:
    image: exeuntu
    integrations: [github]     # switches clones to github.int.exe.xyz URLs
    tags: [agent-pilot]
```

The generated first-boot script clones the repos, runs the setup steps and
checks, then writes `$HOME/work/.agent-run-ready`. Wait for that marker before
starting agent authentication or work.

## Boundaries

- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` in `env` fail validation: the pilot
  is subscription-auth only, and provider credentials never ride in a template.
- Interactive subscription login (Codex device auth, Claude Code SSH flow) is
  deliberately not templatable; `dispatch` stops at "ready" and prints those
  steps instead of attempting them.
- `rm` only deletes VMs that `dispatch` created (tracked in a run record), and
  it re-checks the provider listing before deleting anything.
- exe.dev caps `--setup-script` at 10KiB; the compiler enforces this. Larger
  setups should move logic into the repos themselves.

## Adding a provider

Write a `compile_<provider>` function in `bin/agent-run` that turns the same
template dict plus a runtime into that provider's calls, and register it in
`ADAPTERS`. Templates gain at most a new block under `providers:`; the neutral
core must keep compiling unchanged for existing providers.

## Tests

```sh
python3 agent-run/tests/test_agent_run.py
```
