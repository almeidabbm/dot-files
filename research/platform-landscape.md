# Remote coding-agent platform landscape

Resolves: [#11](https://github.com/almeidabbm/dot-files/issues/11) (part of #10)
Date: 2026-08-11. All claims cite primary sources (official docs and pricing pages) fetched on that date.

## Question

Which platforms can run **OpenAI Codex CLI** and **Claude Code** interchangeably under three hard constraints:

- **(a) Subscription auth** — agent inference authenticated via personal ChatGPT / Claude subscriptions, not metered API keys.
- **(b) Secrets off the VM** — GitHub, LLM, and other credentials never stored as plaintext on the sandbox VM.
- **(c) No self-hosting** — no infrastructure we operate ourselves.

Scoring criteria: running-app **preview URL**, live **attach/steer**, **diff/draft-PR** flow, **multi-repo** in one sandbox, **CLI-first dispatch**, **cost model**.

## A finding that reframes constraint (b)

Subscription login is itself a plaintext secret on disk:

- Codex CLI stores credentials in `$CODEX_HOME` (typically `~/.codex`) after `codex login`; it also accepts tokens piped via stdin (`--with-api-key`, `--with-access-token`) and a device-code flow ([developers.openai.com/codex/cli/reference](https://developers.openai.com/codex/cli/reference)).
- Claude Code on Linux stores OAuth tokens in `~/.claude/.credentials.json` (mode 0600); only macOS gets the encrypted Keychain. A long-lived token can instead be injected via the `CLAUDE_CODE_OAUTH_TOKEN` env var from `claude setup-token` ([code.claude.com/docs/en/authentication](https://code.claude.com/docs/en/authentication)).

So on **any** DIY sandbox, strict constraint (b) is only satisfiable by injecting short/long-lived tokens per-session (env var or stdin, living in process memory / env, not files) rather than running the interactive login on the VM — or by choosing a platform whose control plane keeps credentials outside the sandbox entirely (only Claude Code on the web documents that: "sensitive credentials such as git credentials or signing keys are never inside the sandbox with Claude Code; authentication is handled through a secure proxy using scoped credentials" — [code.claude.com/docs/en/claude-code-on-the-web](https://code.claude.com/docs/en/claude-code-on-the-web)).

## Category 1 — Managed agent products

The structural problem: almost every managed product runs **only its own agent**, so "Codex CLI and Claude Code interchangeably" fails at the door regardless of other scores.

### OpenAI Codex cloud — fails interchangeability (Codex only)

- **(a) passes for Codex**: Codex (web, CLI, IDE, cloud) is included in ChatGPT plans from Plus up; usage is shared with ChatGPT plan limits, with optional credits after that ([developers.openai.com/codex/pricing](https://developers.openai.com/codex/pricing)). API-key mode exists but has "no cloud features".
- **CLI dispatch**: first-class — `codex cloud` opens an interactive picker, `codex cloud exec` submits a task to a named cloud environment, `codex cloud list` returns recent chats as JSON for scripting ([developers.openai.com/codex/cli/reference](https://developers.openai.com/codex/cli/reference)).
- **Diff/PR**: review summary + diff, "open a pull request when the work is ready"; follow-up messages to running tasks supported ([developers.openai.com/codex/cloud](https://developers.openai.com/codex/cloud)).
- **Preview URL**: not documented. **Multi-repo**: environments are configured per repository.
- **Verdict**: excellent Codex-only pipeline; cannot run Claude Code.

### Claude Code on the web / cloud sessions — fails interchangeability (Claude only)

- **(a) passes for Claude**: research preview for Pro/Max/Team; "There is no separate compute charge for the cloud VM" — usage draws from the subscription's shared rate limits ([code.claude.com/docs/en/claude-code-on-the-web](https://code.claude.com/docs/en/claude-code-on-the-web)).
- **(b) best-in-class**: credential proxy keeps git credentials/signing keys out of the sandbox (quote above).
- **CLI dispatch + attach/steer**: `claude --cloud "task"` dispatches from the terminal; `claude -p "msg" --cloud <id>` queues follow-ups; `claude --cloud <id>` attaches the terminal interactively (gradual rollout); `claude --teleport <id>` pulls session + branch into the local terminal.
- **Diff/PR**: web diff view with inline comments, PR creation, and Auto-fix (agent watches CI failures and review comments on the PR).
- **Preview URL**: none. **Multi-repo**: "`--cloud` works with a single repository at a time".
- **Verdict**: excellent Claude-only pipeline; cannot run Codex.

### Devin (Cognition) — fails (a)

Inference is bundled and billed through Cognition's own plans (Free / Pro $20 / Max $200 / Teams), which resell "access to OpenAI, Claude, and Gemini frontier models" with overage "at API pricing" ([devin.ai/pricing](https://devin.ai/pricing)). It runs the Devin agent, not Codex CLI or Claude Code, and cannot use personal ChatGPT/Claude subscriptions. Eliminated.

### Cursor cloud agents — fails (a)

Requires a paid Cursor plan and is "charged at API pricing for the selected model" ([cursor.com/docs/cloud-agent](https://cursor.com/docs/cloud-agent)) — metered, not subscription-authenticated, and it runs Cursor's agent. Notably strong elsewhere (remote-desktop takeover of the agent's VM, multi-repo tasks, PRs from GitHub/GitLab/Azure DevOps/Bitbucket), but eliminated on the hard constraint.

### Google Jules — fails (a) and interchangeability

Google-account product running Google's own agent in its VM ("an experimental coding agent … clones your code, installs dependencies, and modifies files"), with a `jules` CLI ([jules.google/docs](https://jules.google/docs)). No ChatGPT/Claude subscription auth, no Codex/Claude Code. Eliminated.

### Ona (formerly Gitpod) — passes, as a hybrid

The only large managed platform whose own pricing page documents both sides of the constraint:

- "connect an existing **Codex subscription**", where "your subscription covers model usage while Ona provides environments and compute", and "**Claude Code can be installed and authenticated inside an Ona environment** with Claude billing handled separately by Anthropic, while Ona bills for compute and environments" ([ona.com/pricing](https://ona.com/pricing)).
- Environments are ephemeral, isolated Dev Containers with editor/SSH access, triggered interactively or "on a schedule, on pull request events, or from your issue tracker"; managed Ona Cloud or self-hosted VPC ([ona.com/docs](https://ona.com/docs)) — managed cloud satisfies (c).
- **Cost**: Core from $20/mo, billed in Ona Compute Units covering agent tokens + environment runtime (~1 OCU per 4vCPU/16GB hour); add-ons $10 per 40 OCUs ([ona.com/pricing](https://ona.com/pricing)).
- **Unverified in this pass**: secrets-at-rest handling and preview-URL mechanics (Gitpod heritage suggests env-var injection and port URLs, but I did not fetch those doc pages — verify before committing).

### Terragon — passes (a) for both agents; thin evidence elsewhere

Terragon's docs list both agents as providers: Claude Code runs on a connected Claude subscription ("Connect Your Claude Subscription", [docs.terragonlabs.com/docs/agent-providers/claude-code](https://docs.terragonlabs.com/docs/agent-providers/claude-code)), and "to use Codex, you can connect your ChatGPT Subscription", recommended over an API key ([docs.terragonlabs.com/docs/agent-providers/codex](https://docs.terragonlabs.com/docs/agent-providers/codex)). That makes it the only single-pane managed product found that dispatches **both** CLIs on personal subscriptions. Caveats: docs.terragonlabs.com was serving an **expired TLS certificate** on 2026-08-11 (claims above are from indexed doc content), and I found no primary evidence for preview URLs or terminal attach. Treat as promising but needing a hands-on trial.

## Category 2 — DIY on sandbox providers

All of these pass (a) by construction — you run both CLIs yourself and log in with your subscriptions (Anthropic supports Claude Code on Pro/Max, [support.claude.com](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan); OpenAI includes Codex CLI via ChatGPT sign-in, [developers.openai.com/codex/pricing](https://developers.openai.com/codex/pricing)). All pass (c). Constraint (b) is on you: inject tokens per-session (see finding above) instead of persisting login files.

### exe.dev

- Persistent Linux VMs ("VPS") with root, `apt`, `systemd`, reached via `ssh exe.dev`; disposable per-second Sandbox VMs; the Shelley web agent is optional — the VM is yours, so both CLIs run fine ([exe.dev](https://exe.dev/)).
- **Preview URL**: services get HTTPS via the exe.dev proxy with IAM-based sharing ([exe.dev/docs/proxy](https://exe.dev/docs/proxy); page content is JS-rendered — mechanics confirmed only at title/homepage level in this pass).
- **Attach/steer**: SSH is the native model — run the agent in tmux, attach from anywhere. **Multi-repo**: unlimited, it's a full VM. **CLI dispatch**: "API first"; VM creation via SSH/API (this repo's `agent-run` tooling already dispatches through the exe.dev gateway).
- **Cost**: flat **$20/mo Personal** — 50 VMs sharing a pooled 100 GB disk / 200 GB transfer; extra disk $0.08/GB/mo ([exe.dev/pricing](https://exe.dev/pricing)). Flat pool beats per-second metering for long-lived dev VMs.
- **(b)**: nothing platform-side stores your agent tokens; you must inject them (env/stdin) rather than `login` on the VM.

### GitHub Codespaces

- Per-codespace dedicated VM ("Two codespaces are never co-located on the same VM"), isolated virtual network ([docs.github.com/en/codespaces/reference/security-in-github-codespaces](https://docs.github.com/en/codespaces/reference/security-in-github-codespaces)).
- **(b) strongest DIY story**: development secrets are stored by GitHub and "accessed as environment variables in the codespace" (not files); GitHub auth uses a **fresh, expiring, repo-scoped GITHUB_TOKEN minted per session** — no PAT ever touches disk (same source).
- **CLI dispatch + attach**: `gh codespace create -r owner/repo -b branch`, `gh codespace ssh`, `gh codespace ports forward`, `cp`, `logs` ([docs.github.com/…/using-github-codespaces-with-github-cli](https://docs.github.com/en/codespaces/developing-in-a-codespace/using-github-codespaces-with-github-cli)).
- **Preview URL**: forwarded ports with private / org / public visibility; private URLs gated by GitHub auth cookies (security doc above).
- **Multi-repo**: one primary repo per codespace, but additional repos can be cloned with authorized multi-repo token scoping (security doc above).
- **Cost**: usage-based — $0.18/hr for 2-core, $0.07/GB-month storage, with **120 free core-hours/mo (Free) or 180 (Pro)** for personal accounts ([docs.github.com/en/billing/concepts/product-billing/github-codespaces](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces)).

### E2B

- API-key-created Linux VM sandboxes via SDK/CLI ([docs.e2b.dev](https://docs.e2b.dev/)); any CLI runs inside.
- **Preview URL**: `sandbox.getHost(port)` returns a public host for HTTP/WebSocket ([e2b.dev SDK reference](https://e2b.dev/docs/sdk-reference/js-sdk/v1.13.0/sandbox)).
- **Cost**: per-second (1 vCPU ≈ $0.000014/s ≈ $0.05/hr + RAM), $100 one-time free credits; **sessions capped at 1 h (Hobby) / 24 h (Pro, $150/mo)** ([e2b.dev/pricing](https://e2b.dev/pricing)).
- Session caps and SDK-first ephemerality make it a code-execution primitive, not a persistent agent workstation. Not eliminated by the hard constraints, but a poor fit for the criteria (attach/steer and long-lived multi-repo work are DIY plumbing).

### Daytona

- Sandboxes via SDK/CLI/REST, sub-90ms start, **SSH, VNC, web terminal, and preview URLs for ports** are first-class, with stateful snapshots for persistence ([daytona.io/docs](https://www.daytona.io/docs)).
- **Cost**: usage-based per-resource with $200 free credit ([daytona.io/pricing](https://www.daytona.io/pricing)).
- Closest E2B-class rival for this use case because interactive access (SSH/preview) is native; same (b) caveat as all DIY.

### Modal Sandboxes

- "Secure containers for executing untrusted user or agent code"; secrets injected as env vars via `modal.Secret`; volumes for persistence — but sandbox lifetime is **capped at 24 h** ([modal.com/docs/guide/sandbox](https://modal.com/docs/guide/sandbox)). Port exposure (Tunnels) not verified in this pass. Built for batch agent execution, not persistent attachable dev VMs. Weak fit.

### Fly Machines

- Per-second-billed VMs (shared-cpu-1x ≈ $2/mo if always on; stopped machines cost only rootfs storage ~$0.15/GB/30d) ([fly.io/docs/about/pricing](https://fly.io/docs/about/pricing/)).
- **(b) notable**: secrets live in an encrypted vault ("API servers can only encrypt; they cannot decrypt") and are "inject[ed] into your Machine as environment variables at boot time" — never on disk unless you opt in ([fly.io/docs/apps/secrets](https://fly.io/docs/apps/secrets/)).
- Public HTTPS routing, `flyctl` CLI, `fly ssh console` attach. Everything is assemble-it-yourself (image, git auth, agent install); it's IaaS, not a dev-env product. Viable fallback, more plumbing than exe.dev/Codespaces.

## Scoring matrix

| Platform | Runs both CLIs on subs (a) | Secrets off VM (b) | Preview URL | Attach/steer | Diff/PR flow | Multi-repo | CLI dispatch | Cost model |
|---|---|---|---|---|---|---|---|---|
| Codex cloud | No (Codex only) | Managed | Not documented | Follow-ups | Yes + PR | No (per-repo envs) | `codex cloud exec` | Included in ChatGPT plan |
| Claude Code web | No (Claude only) | Yes (credential proxy) | No | `--cloud` attach/queue, `--teleport` | Yes + PR + Auto-fix | No (single repo) | `claude --cloud` | Included in Claude plan |
| Devin | No | Managed | Yes (browser tool) | Yes | Yes | ? | Devin CLI | Reseller plans — fails (a) |
| Cursor cloud | No | Managed secrets | Desktop takeover | Yes | Yes | Yes | No CLI documented | API-metered — fails (a) |
| Jules | No | Managed | No | Limited | Yes | Repo picker | `jules` CLI | Google plans — fails (a) |
| **Ona** | **Yes (documented)** | Managed env secrets (verify) | Likely (verify) | Yes (IDE/SSH) | Yes (PR triggers) | Per-env devcontainer | Partial | $20/mo + OCUs |
| **Terragon** | **Yes (both providers)** | Managed (verify) | Unknown | Web sessions | PR flow | Unknown | Unknown | Subscription + connected plans |
| **exe.dev** | Yes (BYO CLIs) | DIY token injection | Yes (HTTPS proxy + IAM) | Yes (SSH/tmux) | DIY (`gh pr`) | Yes (full VM) | Yes (SSH/API) | Flat $20/mo pool |
| **Codespaces** | Yes (BYO CLIs) | Best DIY (env-var secrets, ephemeral scoped token) | Yes (port visibility tiers) | Yes (`gh codespace ssh`) | DIY (`gh pr`) | Partial (multi-repo access) | Yes (`gh codespace`) | 120–180 free core-hrs, then $0.18/2-core-hr |
| e2b | Yes (BYO CLIs) | DIY | Yes (`getHost`) | DIY | DIY | Yes | SDK/CLI | Per-second + $150/mo Pro; 24 h cap |
| Daytona | Yes (BYO CLIs) | DIY | Yes | Yes (SSH/VNC) | DIY | Yes | Yes | Per-second, $200 credit |
| Modal | Yes (BYO CLIs) | Env-var secrets | Unverified | Exec only | DIY | Yes | SDK | Per-second; 24 h cap |
| Fly Machines | Yes (BYO CLIs) | Vault → env vars at boot | Yes (Fly proxy) | Yes (`fly ssh`) | DIY | Yes | `flyctl` | Per-second, ~$2–32/mo |

## Shortlist

1. **exe.dev** (DIY, primary) — persistent root VMs at a flat $20/mo pooled price, SSH-native attach, HTTPS preview proxy with IAM sharing, no session-length caps, full freedom to run both CLIs on subscription auth; this repo's `agent-run` tooling already targets it. Weakness: secrets discipline is entirely ours (inject `CLAUDE_CODE_OAUTH_TOKEN` / `codex login --with-access-token` per session), and proxy/IAM details need one hands-on verification pass.
2. **GitHub Codespaces** (DIY, co-primary) — the best DIY answer to constraint (b): platform-held secrets surfaced only as env vars plus an ephemeral repo-scoped GitHub token minted per session, so no GitHub PAT ever exists on the VM. Full `gh codespace` CLI dispatch/SSH/port-forward, tiered preview URLs, 120–180 free core-hours monthly. Weakness: metered beyond quota; one primary repo per codespace.
3. **Ona** (managed hybrid) — the only major managed platform whose pricing page explicitly blesses both patterns: connect an existing Codex subscription, install/auth Claude Code inside the environment with Anthropic billing separate. Real dev environments (devcontainers, SSH, PR/issue triggers). Weakness: OCU metering on top of subscriptions; secrets and preview mechanics unverified in this pass.
4. **Terragon** (managed, probational) — the only single product found that dispatches both Claude Code and Codex as pluggable providers on personal subscriptions. Weakness: no primary evidence for preview URLs, terminal attach, or CLI dispatch, and their docs site had an expired TLS cert during research — needs a trial before trusting.

**Key eliminations**: Devin, Cursor cloud agents, and Jules all fail hard constraint (a) — inference is metered/resold through their own billing and none can run either CLI under a personal subscription. Codex cloud and Claude Code on the web each pass (a) superbly for their own agent but are single-agent walled gardens; running them **side by side** (both included in subscriptions already held, both with real CLI dispatch: `codex cloud exec` / `claude --cloud`) is a legitimate zero-extra-cost fallback if "one platform" is negotiable — their shared gap is no preview URL for a running app. E2B and Modal aren't constraint violations but their 24 h session caps and execution-primitive design fit the criteria poorly; Daytona and Fly Machines are credible backups if exe.dev disappoints.
