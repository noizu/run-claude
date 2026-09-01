# Project Architecture Summary

run-claude provides directory-aware model routing for Claude Code and OpenCode via a self-healing local LLM gateway. Entering a directory with a declared profile registers models with the gateway and sets environment variables routing Claude Code or OpenCode through it. Default model layer is the **unified go-litellm gateway** (single static binary on :4443); `FRONT_PROXY_COMMAND=python|legacy` falls back to the old front-proxy → LiteLLM chain. A self-healing watchdog daemon keeps the gateway alive either way.

## Components

- **CLI** (`cli.py`): Subcommands — enter, leave, janitor, set-folder, status, env, proxy, db, profiles, models, keys, chat, with, install, secrets.
- **OpenCode CLI** (`opencode_cli.py`): `run-open-code` entry point sharing the same command handlers.
- **Agent runner** (`agent_runner.py`): Shared Claude/OpenCode launch logic; sets ANTHROPIC_BASE_URL to :4443 and per-tier model vars.
- **Chat client** (`chat.py`): Interactive terminal chat against the local gateway; model picker, `/keys` switching.
- **Profiles** (`profiles.py`): Multi-file YAML loading with fallthrough (user override > user > built-in). Maps opus/sonnet/haiku/fable tiers to model definitions.
- **State** (`state.py`): JSON persistence for tokens, refcounts, model leases, key swaps, PIDs, stop marker.
- **Proxy lifecycle** (`proxy.py`): Gateway start/stop + health; resolves go-litellm (default), ex-litellm override, or legacy Python chain.
- **Key switching** (`keys.py`): Named provider keys from `<FAMILY>_SUB_KEY[_SUFFIX]` env vars, swapped live against go-litellm without changing model ids.
- **Unified Go gateway** (`repos/go-litellm`, vendored binary `run_claude/bin/go-litellm`): Default one-process endpoint + provider routing (wafer.ai, z.ai, Groq, Anthropic, OpenAI-compatible) with runtime named-key registry.
- **Front proxy** (`front_proxy.py`, legacy): Reverse proxy :4443 → :4444; passthrough mode forwards Anthropic models to api.anthropic.com with original OAuth auth.
- **Watchdog** (`watchdog.py`): Detached daemon restarting gateway process(es) when down; a stop.marker sentinel distinguishes intentional stops from crashes.
- **LiteLLM launcher** (`litellm_proxy.py`): `run-litellm-proxy` entry; prisma schema patching then exec litellm (legacy).
- **Config** (`config.py`): Secrets (mode 0600), .env generation, env var hydration.
- **Hooks** (`hooks/`): Lifecycle hook chain (PRE_REQUEST, POST_RESPONSE, PRE/POST_TOOL_CALL) with error isolation.
- **Provider Compat** (`callbacks/provider_compat.py`): Strips unsupported fields for strict providers; runs in the legacy LiteLLM proxy process.

## Key Patterns

- Stable tokens via SHA256 hash of directory path
- Refcount with 15-min lease prevents model thrashing
- `os.environ/VAR` syntax hydrated at runtime
- Multi-file config fallback with `model: null` disable
- Named-key indirection: env var → canonical name → family/model binding
- Stop-marker sentinel: watchdog honors intentional stops, auto-restarts crashes
- Hook chain with error isolation

## Infrastructure

- Gateway endpoint: `127.0.0.1:4443` (go-litellm by default; binary resolution: vendored → PATH → ~/.local/bin → source build)
- Legacy chain: front proxy `:4443` + LiteLLM `:4444` + TimescaleDB (Docker, port `5433`; extensions vector, pg_trgm)
- Config: `~/.config/run-claude/` (XDG); State: `~/.local/state/run-claude/` (XDG)

## Ecosystem Fit

Lives at `Portfolio/Utilities/source/run-claude` in the Noizu Infra monorepo (dual install path under `utilities/`) but is not part of the shell-utility toolchain: no k8-lib, not installed by `make install-utilities`, no `.infra-config.yaml` target. Self-contained Python package (hatchling + uv) installed via `make install` (`uv tool install .`); console scripts: run-claude, run-open-code, run-litellm-proxy. Provides per-directory provider routing (wafer, z.ai, Groq, Cerebras, Ollama, mixed) for agent sessions working on the monorepo. go-litellm source pinned as submodule at `repos/go-litellm`; Elixir alternative `repos/ex-litellm`. Landing site: Elixir Hologram app in `web/` deployed via `helm/run-claude-landing`.

## Detailed Docs

- [arch/data-flows.md](arch/data-flows.md) — Mermaid flow diagrams for enter/leave/janitor/resolution
- [arch/design-patterns.md](arch/design-patterns.md) — Pattern details with code examples
- [arch/infrastructure.md](arch/infrastructure.md) — Network, env vars, process lifecycle, security
