---
name: agent-run-template
description: Use when writing or changing an agent-run sandbox template — describing a new remote-agent VM, adding a repository or credential to an existing one, or fixing a template whose dispatch failed during setup.
---

# Write an agent-run template

A template describes what a remote agent's VM needs; `agent-run` compiles it into
one first-boot script. That script is the whole environment — everything the
agent finds on the box was cloned, installed, or written by it — and it gets one
attempt, unattended, on a machine with no terminal to answer a prompt.

So the work is front-loaded: get it right before a VM exists. `validate` and
`compile` touch no provider and cost nothing. `dispatch` creates a real VM.

`agent-run/templates/schema.json` is the authority on what a template may
contain. Read it rather than recalling fields, and add nothing it does not
define — `additionalProperties` is false throughout, so an invented field is a
hard failure. `agent-run/README.md` explains the fields the schema only names.

## 1. Establish what the environment needs

Ask about anything below the user has not already said. Each answer maps to one
part of the template, and a wrong guess here is what a failed dispatch is made
of.

| Ask | Decides |
| --- | --- |
| Which repositories, and which one does the agent work in? | `repos`, and which carries `role: primary` |
| Is each one public, or does it need credentials? | The **clone route** — see below |
| Which branch, if not the default? | `ref` per repo |
| Codex, Claude, or either? | `runtimes` |
| What must be installed before the code will build or test? | `setup`, and the `checks` that prove it |
| How heavy is the build? | `resources` |

For an existing template, read it first and change only what the request
touches. A template that already dispatches is evidence; treat it as such.

## 2. Choose the clone route per repo

Three routes, in order of preference. Each repo takes exactly one.

| Route | Declare | Use when |
| --- | --- | --- |
| Anonymous | nothing | The repo is public |
| exe.dev integration | `private: true` on the repo, and the integration name under `providers.exe.dev.integrations` | The repo is private on github.com and the account has an integration for it. Best available: the credential is injected at the network layer and is never on the VM |
| Credential | `auth: <SECRET_NAME>` on the repo, plus a `secrets:` entry of `type: git-credential` with a matching `host` | No integration covers the host, or the task needs a token scoped differently from the integration |

Reach for the integration whenever one exists. Nothing beats a credential that
was never on the box.

Taking the credential route pulls in two obligations:

- The name in `auth:` must match a `secrets:` entry whose `host` equals the
  repo's host, or `validate` refuses it.
- The user must have registered that name on their machine:
  `agent-run secret set <NAME> --command '<command that prints it>'`. Check with
  `agent-run secret ls` and say so if it is missing — a template naming an
  unregistered secret fails at dispatch, before the VM is created.

A repo may set `private:` or `auth:`, never both. They are two routes to the same
place, and the schema refuses the pair rather than silently picking one.

## 3. Place each setup step

The boot script runs in a fixed order, and where a step goes decides whether what
it needs already exists:

```text
clones -> REPOS.md -> template-wide setup -> per-repo setup -> checks -> ready marker
```

| A step that | Goes in | Because |
| --- | --- | --- |
| Provisions the box — a language runtime, a package manager, a system package | top-level `setup:` | It runs first, so everything downstream can rely on it |
| Installs one repo's dependencies | that repo's own `setup:` | It runs last, in that checkout, after the box is provisioned |
| Spans repos, or must run before a repo's own steps | top-level `setup:` with `cwd:` | Only the top-level list can be ordered against other repos |

Two facts about the image shape most templates: `exeuntu` ships git, tmux, and
the agent CLIs but **no node or npm**, and Ubuntu's own `nodejs` is too old for
most work — install from NodeSource in a top-level step. And put
`configure-llm-integration` in every template, first: without it the runtime has
no model access and someone has to log in on the VM by hand.

Write `checks:` for the things a task will actually depend on. Each must exit 0
before the VM is declared ready, so a check is how a broken environment fails at
dispatch instead of ten minutes into an agent's run. Prove the tools exist
(`node --version`, `pnpm --version`), not that the machine boots.

## 4. Write the file

Save to `agent-run/templates/<name>.yaml`, where `<name>` matches the template's
own `name:` field. Comment the decisions that are not obvious from the value —
why this node version, why this integration, why the timeout will be long. The
shipped templates set the standard for this; read `lightdash-dev.yaml`.

Keep every value whitespace-free. `ssh` joins remote arguments with spaces and
exe.dev's parser has no quoting, so a template `env` value like `hello world`
fails at compile time.

## 5. Prove it before spending a VM

```sh
agent-run validate agent-run/templates/<name>.yaml
agent-run compile agent-run/templates/<name>.yaml --runtime codex --script-out /tmp/<name>.sh
```

`validate` runs the schema, the repo checks, the secret checks, and the
forbidden-env check, then reports the setup script against exe.dev's 10 KiB cap.
`compile` writes the script it would send. **Read that script.** It is the
environment; reading it is the only review it will ever get.

Check, in the generated script:

- Every repo is cloned, to a distinct directory, at the intended ref.
- The steps are in an order where each one's prerequisites already exist.
- No credential appears anywhere in it.
- The size leaves room — near 80% of the cap, say so.

This step is done when `validate` passes for every runtime the template allows
and the compiled script has been read. Report the size, then stop: `dispatch`
creates a billable VM and is the user's call, not yours.

## Edge cases

- **More than one repo and no `role: primary`** — refused, deliberately. Ask
  which one the agent works in rather than picking the first.
- **Two repos with the same name** (`org-a/api`, `org-b/api`) — they collide on
  one checkout directory. Give all but one an explicit `path:`.
- **A credential-shaped `env:` name** — refused. `env` is plaintext on the VM and
  in the agent's own environment; move it to `secrets:`.
- **A slow install** (`pnpm install` on a monorepo) — the template is fine, but
  say that dispatch needs `--wait-timeout 1800`, and put it in a comment.
- **Fixing a template whose dispatch failed** — read
  `agent-run logs <name> --source setup` first. The failing command is in there,
  and it names the step to change.
