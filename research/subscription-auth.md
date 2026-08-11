# Subscription auth for Codex CLI and Claude Code on remote machines

Research for [#12](https://github.com/almeidabbm/dot-files/issues/12) (part of #10).
Question: how can Codex CLI and Claude Code authenticate on a remote sandbox/VM with a
personal ChatGPT / Claude subscription — without an interactive per-VM login and without
plaintext credentials sitting on the VM?

All claims cite primary sources (official docs, provider ToS, vendor docs). Researched 2026-08-11.

---

## 1. Official login flows on a headless remote machine

### Codex CLI

Source: [Codex authentication docs](https://developers.openai.com/codex/auth) (canonical URL; currently serves from learn.chatgpt.com/docs/auth).

- **Standard flow**: `codex login` starts a local callback server on `localhost:1455` and
  opens a browser; the browser returns credentials to the CLI.
- **Device-code flow (beta)**: `codex login --device-auth` prints a URL plus a one-time code
  you approve from any browser — no callback port, no port forwarding. Device-code
  authorization must be enabled in ChatGPT security settings (personal) or workspace
  permissions (workspace admin).
- **SSH port forwarding**: `ssh -L 1455:localhost:1455 user@remote`, then run `codex login`
  on the remote and open the printed `http://localhost:1455/...` URL in the local browser.
- **Storage**: `$CODEX_HOME/auth.json` (default `~/.codex/auth.json`), or the OS keyring with
  `cli_auth_credentials_store = "keyring"`. The docs say to treat `auth.json` "like a
  password: it contains access tokens."
- **Refresh**: "Codex refreshes tokens automatically during use before they expire, so active
  sessions usually continue without requiring another browser login."
- **API key alternative**: `printenv OPENAI_API_KEY | codex login --with-api-key` — but that
  is platform billing, not the ChatGPT subscription.

### Claude Code

Source: [Claude Code authentication docs](https://code.claude.com/docs/en/authentication).

- **Standard flow**: `claude` opens a browser to log in with the Claude.ai account. On a
  headless box, press `c` to copy the login URL, open it anywhere; "If your browser shows a
  login code instead of redirecting back... paste it into the terminal at the `Paste code
  here if prompted` prompt. This happens when the browser can't reach Claude Code's local
  callback server, which is common in WSL2, SSH sessions, and containers." So the login
  completes over SSH with no port forwarding — URL out, code back in.
- **Long-lived token**: `claude setup-token` runs the same browser authorization as `/login`
  and prints a **one-year OAuth token**; it is not saved anywhere — you export it as
  `CLAUDE_CODE_OAUTH_TOKEN` wherever you want to authenticate. "Use this for CI pipelines and
  scripts where browser login isn't available." Requires Pro/Max/Team/Enterprise. It can only
  make model requests (no Remote Control, no claude.ai connectors). Bare mode (`--bare`) does
  not read it.
- **Storage**: macOS Keychain; on Linux `~/.claude/.credentials.json` mode `0600`
  (or under `CLAUDE_CONFIG_DIR`).
- **Lifetime**: `/login` credentials expire; Claude Code warns 3 days out
  ("Your login expires in 3 days · run /login to renew") and requests fail with
  `Login expired · Please run /login` once refresh is no longer possible. Unattended sessions
  that outlive the login stop making progress.
- **Auth precedence** (high to low): cloud-provider creds → `ANTHROPIC_AUTH_TOKEN` →
  `ANTHROPIC_API_KEY` → `apiKeyHelper` script → `CLAUDE_CODE_OAUTH_TOKEN` → `/login` OAuth.

Both CLIs therefore *can* complete a real login on a headless VM (Codex via device code or
port forward; Claude Code via printed-URL + pasted code), but that is an interactive step per
VM — which is exactly what the ticket wants to avoid.

## 2. Auth-cache / credential-file reuse

- **Codex**: officially sanctioned. The auth docs describe transferring `~/.codex/auth.json`
  between machines with `scp` or into Docker; community/official guidance notes the file "is
  not tied to a specific host," so a locally-completed login can be copied to a headless
  machine and Codex "just works" ([auth docs](https://developers.openai.com/codex/auth),
  [mirrored authentication.md](https://github.com/amchii/codexx/blob/main/docs/authentication.md)).
  Cost: a plaintext refresh-token file at rest on the VM (unless the keyring store is used,
  which doesn't survive copying). Auto-refresh means the copy stays valid indefinitely under
  use — and also means the VM holds a credential that can mint fresh tokens.
- **Claude Code**: copying `~/.claude/.credentials.json` between Linux hosts works in practice
  (widely documented in the community, e.g.
  [this gist](https://gist.github.com/Prajwalsrinvas/cacbb728c4ea06c3bc1676608d3c72dc)), but
  unlike Codex it is **not** a documented/supported workflow — the docs say the file is
  "managed through `/login` and `/logout`". The supported equivalent is `claude setup-token`
  → `CLAUDE_CODE_OAUTH_TOKEN` (above), which is explicitly designed for exactly this case.
- **ToS standing**: reusing *your own* credential on *your own* second machine, inside the
  first-party CLI, is consistent with both providers' terms; what both prohibit is sharing
  the credential with anyone else (see §6). It still fails the ticket's "no plaintext
  credentials on the VM" bar: `auth.json` / `.credentials.json` / an exported
  `CLAUDE_CODE_OAUTH_TOKEN` env var are all readable by anything running on the VM —
  including the agent itself.

## 3. Cloud-native subscription binding (no credential ever reaches the sandbox)

- **Codex cloud**: tasks run in OpenAI-managed sandboxes bound to your ChatGPT account —
  you start work at [chatgpt.com/codex](https://chatgpt.com/codex), from GitHub PRs, Linear,
  Slack, or from Codex CLI, and "start and review work from the web or Codex CLI"
  ([Codex cloud docs](https://developers.openai.com/codex/cloud)). Authentication is your
  ChatGPT web session; the sandbox itself carries no subscription credential.
- **Claude Code on the web** ([docs](https://code.claude.com/docs/en/claude-code-on-the-web)):
  sessions run "in an isolated, Anthropic-managed VM" tied server-side to your claude.ai
  account. The credential-protection guarantee is explicit: "sensitive credentials such as
  git credentials or signing keys are never inside the sandbox with Claude Code;
  authentication is handled through a secure proxy using scoped credentials." Inference
  always uses your subscription: "Claude Code on the Web always uses your subscription
  credentials. If you set `ANTHROPIC_API_KEY` ... in the sandbox environment, it doesn't
  override your subscription credentials." Start sessions with `claude --cloud "task"`,
  steer with `claude -p "msg" --cloud <session-id>`, pull down with `claude --teleport`.
  GitHub access goes through the Claude GitHub App or a `gh` token synced via `/web-setup` —
  again held server-side, not in the sandbox.

This is the only category where the provider *itself* keeps the subscription binding entirely
out of the sandbox. The trade-off: you get the provider's managed environment, not your own VM.

## 4. Gateway / integration approaches

### exe.dev LLM integration (network-edge secret injection)

Sources: [What are Integrations?](https://exe.dev/docs/integrations),
[LLM Integration guide](https://exe.dev/docs/integrations-llm),
[LLM Gateway](https://exe.dev/docs/shelley/llm-gateway).

- Model: "the secret is stored server-side and injected at the network edge when your VM
  calls the integration hostname. The VM — and any agent running on it — can *use* the
  integration but can never read the secret." Integration hostnames are
  `https://<name>.int.exe.xyz` (the host resolves to the 169.254.169.254 metadata range, so
  it only works from inside an attached VM).
- Provider sources per integration: `exe.dev LLM gateway` (managed allocation), `API Key`
  (BYOK, key unreadable from the VM), `ChatGPT subscription`, or `Disabled`.
- **ChatGPT subscription source**: "connect a ChatGPT account and use it as the OpenAI source
  for a personal LLM integration." It uses **ChatGPT's official device-code authorization
  flow** (`integrations setup chatgpt --name work` prints a chatgpt.com URL + one-time code;
  device-code login must be enabled in ChatGPT security settings). "The ChatGPT account is
  connected to exe.dev, not to the VM. Codex still talks to the integration hostname without
  an OpenAI API key in the VM." Personal integrations only; team integrations are limited to
  gateway or API keys.
- **Codex through it — verified working** in this repo's `agent-run` tooling: custom provider
  with `base_url = "https://llm.int.exe.xyz/v1"`, `requires_openai_auth = false`,
  `wire_api = "responses"` (the gateway exposes `/v1/responses` and `/v1/messages`).
- **Anthropic subscription source: does not exist.** The integration supports Anthropic only
  via the managed gateway or a Console **API key** (`--anthropic=byok`). Claude Code is then
  pointed at the gateway with `ANTHROPIC_BASE_URL=https://llm.int.exe.xyz` plus a placeholder
  key (`apiKeyHelper: "printf exe-gateway"`). Given Anthropic's policy (§6), a "Claude
  subscription source" cannot legitimately exist at any gateway — this is a policy wall, not
  an exe.dev gap.
- Near-equivalent for Claude subscriptions worth noting: exe.dev's **HTTP Proxy Integration**
  "inject[s] headers into HTTP requests." In principle a `claude setup-token` one-year token
  could be held at the gateway and injected as the `Authorization` header, with
  `ANTHROPIC_BASE_URL` pointed at the integration — the client is still first-party Claude
  Code using your own subscription token, and no credential sits on the VM. Unverified, and
  gray: Anthropic scopes OAuth to "ordinary use of Claude Code," and a header-injecting relay
  is a third-party service in the request path.

### Other gateways (LiteLLM etc.)

- **LiteLLM ChatGPT provider** ([docs](https://docs.litellm.ai/docs/providers/chatgpt)):
  first-class `chatgpt/*` models using OAuth device-code login against the "ChatGPT backend
  API"; "tokens are stored locally for reuse" — i.e. the subscription token sits on the proxy
  host, and any client (including Claude Code pointed at LiteLLM) can consume ChatGPT
  subscription inference. This is a *non-Codex client* on the ChatGPT backend — see ToS §6.
- **LiteLLM Claude Max passthrough**
  ([tutorial](https://docs.litellm.ai/docs/tutorials/claude_code_max_subscription)):
  `forward_client_headers_to_llm_api: true` forwards Claude Code's own subscription OAuth
  `Authorization` header through the proxy to Anthropic. The token stays on the Claude Code
  machine, but requests are routed "through" a third-party service — squarely in the zone
  Anthropic now prohibits (§6).
- No gateway can front a Claude subscription in a compliant way today; for Anthropic the
  compliant gateway input is an API key ([LLM gateway docs](https://code.claude.com/docs/en/llm-gateway)-style
  `ANTHROPIC_BASE_URL`/`ANTHROPIC_AUTH_TOKEN` deployments).

## 5. Ranking (friction × security posture)

For the ticket's constraint — no per-VM interactive login, no plaintext credential on the VM:

1. **Provider cloud sandboxes** (Codex cloud; Claude Code on the web / `claude --cloud`).
   Zero credential in the sandbox by design, server-side subscription binding, fully
   supported. Friction: you accept the provider's managed environment instead of your own VM.
2. **exe.dev LLM integration with ChatGPT subscription source** (Codex on your own VM).
   Official device-code flow, token held at the gateway, VM can use but never read it;
   verified working with `base_url=https://llm.int.exe.xyz/v1`, `wire_api="responses"`.
   Friction: one-time device-code connect + Codex provider config. Minor residual: your
   ChatGPT token is custodied by exe.dev (personal integrations only).
3. **`claude setup-token` → `CLAUDE_CODE_OAUTH_TOKEN`** (Claude Code on your own VM). The
   only Anthropic-supported non-interactive subscription mechanism: one browser approval
   yields a 1-year token, injected as an env var at VM provision time. Friction: near zero
   day-to-day. Security: the token is readable on the VM (env), so it fails the strict
   "never on the VM" bar — mitigate by scoping it to short-lived VMs, or (unverified,
   gray-zone) holding it at an exe.dev HTTP-proxy integration and injecting the header at
   the network edge.
4. **Codex `auth.json` copy** (or `codex login --device-auth` once per VM). Officially
   documented and refresh-capable, but a plaintext refresh credential at rest on the VM;
   device-auth avoids the file copy at the cost of one interactive approval per VM.
5. **Claude `.credentials.json` copy**. Works, but undocumented/unsupported, plaintext on the
   VM, and expires on the normal `/login` cadence — strictly worse than option 3.
6. **Third-party subscription-fronting proxies** (LiteLLM `chatgpt/*`, LiteLLM Claude-Max
   OAuth passthrough, opencode-style clients). Lowest standing: prohibited on the Anthropic
   side, gray-to-prohibited on the OpenAI side (§6). Not recommended regardless of how well
   they work technically.

## 6. ToS red flags

- **Anthropic — explicit prohibition on third-party subscription use.** The Claude Code
  [legal and compliance page](https://code.claude.com/docs/en/legal-and-compliance): "OAuth
  authentication is intended exclusively for purchasers of Claude Free, Pro, Max, Team, and
  Enterprise subscription plans and is designed to support ordinary use of Claude Code and
  other native Anthropic applications. ... Anthropic does not permit third-party developers
  to offer Claude.ai login or to route requests through Free, Pro, or Max plan credentials on
  behalf of their users. Anthropic reserves the right to take measures to enforce these
  restrictions and may do so without prior notice." Enforcement is active: consumer-plan
  OAuth in third-party clients began being blocked in early 2026, and Anthropic announced
  subscriptions stop covering third-party tool usage as of April 4, 2026
  ([alternativeto.net news summary](https://alternativeto.net/news/2026/2/anthropic-officially-bans-using-subscription-authentication-for-third-party-claude-use)).
  ⇒ LiteLLM Claude-Max passthrough, opencode-style clients, and any hypothetical gateway
  "Claude subscription source" are ToS violations. First-party Claude Code on your own VM
  (login, setup-token, cloud sessions) is fine.
- **Anthropic — account sharing.** [Consumer Terms](https://www.anthropic.com/legal/consumer-terms):
  "You may not share your Account login information, Anthropic API key, or Account
  credentials with anyone else," and you "may not make your Account available to anyone
  else." ⇒ don't put your subscription credential on shared/multi-user VMs.
- **OpenAI — account sharing.** [Terms of Use](https://openai.com/policies/row-terms-of-use/):
  "You may not share your account credentials or make your account available to anyone else
  and are responsible for all activities that occur under your account" (see also the
  [Account Sharing Policy](https://help.openai.com/en/articles/10471989-openai-account-sharing-policy)).
  Copying `auth.json` to your own VM is documented and fine; letting others use that VM's
  credential is not.
- **OpenAI — non-Codex clients on the ChatGPT backend.** LiteLLM's `chatgpt/*` provider (and
  similar bridges that let Claude Code consume a ChatGPT subscription) drive the consumer
  backend from unofficial clients. OpenAI has no published equivalent of Anthropic's explicit
  ban, but this is outside the documented Codex auth surface and carries account-action risk;
  the exe.dev ChatGPT source is materially safer because it rides the official device-code
  authorization that ChatGPT lets you enable/disable in security settings.
- **Third-party token custody (exe.dev).** Even for the sanctioned ChatGPT source, your
  subscription tokens live with Bold Software's gateway. OpenAI's terms don't explicitly
  address delegated custody; treat it as personal-use gray space and keep the integration
  personal, revocable (device-code toggle + `integrations setup chatgpt --delete`).

## 7. Practical answer for this repo's `agent-run` stack

- **Codex on exe.dev VMs**: keep the current setup — LLM integration with
  `--openai=chatgpt`, provider `base_url=https://llm.int.exe.xyz/v1`, `wire_api="responses"`,
  `requires_openai_auth = false`. No credential on the VM, no per-VM login, ToS-clean.
- **Claude Code on exe.dev VMs**: no subscription-equivalent exists. Compliant options today:
  (a) `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token` injected at provision time
  (subscription-billed, token readable on-VM, 1-year life), or (b) an Anthropic **API key**
  behind the exe.dev LLM integration (`--anthropic=byok` + `ANTHROPIC_BASE_URL`) — key never
  on the VM, but Console-billed, not subscription. For genuinely credential-free subscription
  use, hand the task to Claude Code on the web (`claude --cloud`) instead of the VM.
