# agent-run

Code-driven, provider-agnostic sandbox templates for remote coding agents.

A **template** (`templates/*.yaml`, validated by `templates/schema.json`)
describes what an environment needs — resources, repositories, allowed
runtimes, env, setup steps, readiness checks — without saying anything about
how a given provider builds it. A **provider adapter** compiles the template
into concrete lifecycle calls. The coding-agent runtime (Codex or Claude Code)
is a dispatch-time flag, not a template fork.

`agent-run` only validates and compiles. It never executes anything against a
provider; you review the printed command and run it yourself.

## Usage

```sh
agent-run/bin/agent-run validate agent-run/templates/lightdash-dev.yaml

agent-run/bin/agent-run compile agent-run/templates/lightdash-dev.yaml \
  --runtime codex
# setup script -> lightdash-dev-codex-setup.sh (447 bytes)
# ssh exe.dev new --json --name=lightdash-dev-codex --cpu=4 ... < lightdash-dev-codex-setup.sh
```

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
  deliberately not templatable; follow the task runbook after the VM is ready.
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
