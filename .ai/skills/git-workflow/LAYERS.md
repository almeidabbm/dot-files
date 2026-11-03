# Layers

A layer is classified by how it fails, not by which folder it lives in. This list is a starting set: when a change fails in a way none of these name, add a layer, and say in the commit body how it fails and how to review it.

## Catastrophic

Read the code. Each of these lands in the PR's risk map.

| Layer | Covers | Fails as | Review by |
| --- | --- | --- | --- |
| `data` | Migrations, schema, persisted models and entities | Lost or corrupted data; rollback that cannot run | Reading the code; migration up and down; old code against the new schema |
| `access` | Authentication, permissions, tenancy, tokens, embed and share scopes | Data visible to the wrong user, org, or embed | Reading the code; tests that the denied case is denied |
| `domain` | Business rules and computation: query building, compilers, aggregation, dates and timezones, money | Wrong numbers with no error | Reading the code and the tests' expected values |
| `contract` | Anything an outside caller depends on: public API, SDK, CLI, MCP tool schemas, file formats | Callers you cannot see break | The contract diff; additive or versioned |

## Silent

Fail quietly or only at scale. Verify with evidence; read the code where the evidence is thin.

| Layer | Covers | Fails as | Review by |
| --- | --- | --- | --- |
| `config` | Env vars, defaults, feature flags | Existing installs break on upgrade | Defaults, renamed or removed variables |
| `integration` | Warehouses, third-party APIs, messaging, webhooks | Breaks for one provider or tenant | Tests or a run against the integration |
| `background` | Schedulers, workers, queues, retries | Duplicated or dropped work, retry storms | Idempotency, retry, and failure paths |
| `agent` | Prompts, AI tools' behaviour, model choice | Quietly worse answers | Evals or recorded runs, not code reading |

## Visible

| Layer | Covers | Fails as | Review by |
| --- | --- | --- | --- |
| `ui` | Components, pages, copy | Visible and quickly reverted | Screenshots or the running app |
| `observability` | Logging, metrics, product analytics | Personal data in logs or events | Skim for what is recorded |

## Skippable

| Layer | Covers | Review by |
| --- | --- | --- |
| `mechanical` | Renames, moves, codegen, formatting, lockfiles, dependency bumps | Confirming it was generated, not hand-edited, and changes no behaviour |
| `tooling` | CI, build, dev scripts, infrastructure as code | The pipeline running green |
