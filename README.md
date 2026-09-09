# run-claude

**Repo:** https://github.com/noizu/run-claude

Per-directory model routing for Claude Code & OpenCode, backed by a self-healing local LLM gateway.

## What

`cd` into a project, get the right models. `run-claude` hot-registers whichever provider models a directory declares (via direnv + a shell hook) on a running gateway, routes all traffic through a front proxy that swaps auth per provider — including Anthropic OAuth passthrough so a Claude Pro/Max subscription is used instead of API billing — and keeps itself alive with a watchdog daemon. 145+ cataloged models across ~25 profiles (see `profiles.yaml`) are one `set-folder` away.

## Why

Different projects want different LLM providers (cost, capability, rate limits), but Claude Code/OpenCode expect one static endpoint. run-claude gives each directory a stable declared profile and a single local endpoint, so agents "just work" anywhere without per-project config drift or leaked per-provider keys.

## Getting Started

Prerequisites: Python 3 + `uv`, Docker (gateway DB), direnv, and the Claude Code and/or OpenCode CLI.

```bash
make install                      # CLI + go-litellm gateway + shell completions
run-claude secrets init --generate   # provider API keys + auto-generated DB password

cd /path/to/my/project
run-claude set-folder cerebras    # writes .envrc; prints your stable dir token
direnv allow                      # activate

claude                            # models registered on entry; just works
run-claude status --health        # verify: proxies, DB, refcounts as JSON
```

Provider keys live in `~/.config/run-claude/.secrets` — see `SECRETS_QUICKSTART.md` / `SECRETS.md` / `SECRETS_ADVANCED.md`. Never commit that file. Tests: `make test` (plus `test-cov`, `coverage-html`).

## How It Works

- **Directory-scoped routing** — `set-folder <profile>` writes `.envrc`; on entry the shell hook calls `run-claude enter`, registering that directory's models on the live gateway. Refcounted with a 15-minute lease, cleaned by the `janitor`.
- **Front proxy (:4443)** — swaps auth per provider: Anthropic requests pass through with the original OAuth token (subscription billing); other providers use the gateway master key. JSONL request logging and persisted auth state included.
- **Gateway (:4444)** — default `go-litellm`: one static CGO-free Go binary serving the front proxy and LiteLLM on one port. Optional Elixir/OTP `ex-litellm` or legacy Python LiteLLM (`make setup-litellm`).
- **Self-healing** — detached watchdog daemon auto-restarts crashed proxies (~5s poll); intentional stops are respected via a `stop.marker` sentinel.

## Command Reference

- `set-folder <profile>` / `enter` / `leave` — per-directory activation and lease management; `janitor` cleans expired leases.
- `status`, `env <profile>` — state and environment introspection (`--health` for JSON health).
- `proxy start|stop|restart|status|health|db-test`, `watchdog start|stop|restart|status` — lifecycle.
- `db start|stop|status|migrate` — gateway database container (Prisma migrations).
- `profiles`, `models list|enabled|show|avail|wipe` — profile and model catalog management.
- `keys list|add|delete|switch` — runtime provider key swap (go-litellm).
- `chat` — multi-turn model tester; `with <profile>` — one-shot agent run; `run-open-code` fronts OpenCode.
- `secrets` — secrets configuration; `install` — user config templates.

## Docs

`docs/` carries PROJ-ARCH / PROJ-HOWTO / PROJ-LAYOUT / PROJ-SCHEMA / PROJ-FAQ (digests + full), PRDs, and per-component arch notes. `playground/`, `helm/`, `templates/`, and `completions/` cover experimentation, k8s deployment, config templates, and shell completion respectively.

License: MIT (see `LICENSE`).
