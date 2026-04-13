# Project Layout

Navigable map of the run-claude project structure.

## Root

```
run-claude/
├── .claude/                 # Claude Code config (agents, commands, settings)
├── docs/                    # Documentation → [layout/docs.md](layout/docs.md)
│   ├── arch/                #   Extracted architecture details
│   ├── layout/              #   Extracted layout details
│   ├── PRDs/                #   Product requirement documents (19 files)
│   └── claude/              #   Claude AI tool specifications
├── dep/                     # Infrastructure (Docker) → See below
├── hooks/                   # Shell integration hooks → See below
├── playground/              # Test directories for profile switching
├── run_claude/              # Main Python package → [layout/run-claude-package.md](layout/run-claude-package.md)
│   ├── callbacks/           #   Provider compatibility (runs in proxy venv)
│   └── hooks/               #   Lifecycle hook system (chain, loader, builtins)
├── scripts/                 # Utility scripts
├── templates/               # direnv templates (envrc.tmpl, envrc.user.tmpl)
├── tests/                   # Test suite → See below
├── .envrc                   # direnv configuration
├── .gitignore               # Git ignore rules
├── .python-version          # Python version for runtime
├── .tool-versions           # asdf version manager config
├── CLAUDE.md                # Claude Code project instructions
├── Makefile                 # Build automation (test, install, refresh)
├── profiles.yaml            # Built-in profile definitions
├── pyproject.toml           # Python project config (hatchling)
├── uv.lock                  # Dependency lockfile
├── README.md                # User guide
├── SECRETS.md               # Secrets configuration guide
├── SECRETS_ADVANCED.md      # Advanced secrets management
├── SECRETS_QUICKSTART.md    # Quick reference for secrets
└── with-agent-shim          # Wrapper script for running with profiles
```

## dep/ — Infrastructure

```
dep/
├── docker-compose.yaml           # TimescaleDB service definition
├── docker-compose.override.yaml  # Dev overrides (port 5433)
├── litellm.Dockerfile            # Custom LiteLLM proxy image
├── .envrc                        # direnv for dep directory
└── config/
    └── timescaledb/
        └── init-databases.sql    # DB init (vector, pg_trgm extensions)
```

Service: TimescaleDB `timescale/timescaledb:2.23.1-pg17`, container `run-claude-timescaledb`, volume `timescaledb-data`, network `run-claude-network`, dev port `5433:5432`.

## hooks/ — Shell Integration

```
hooks/
├── bash_hook.sh   # Bash PROMPT_COMMAND hook
├── zsh_hook.zsh   # Zsh precmd hook
└── install.sh     # Hook installation script
```

Detects `AGENT_SHIM_TOKEN` changes via direnv, calls `run-claude enter/leave`, runs janitor periodically.

## scripts/

```
scripts/
├── run-litellm-proxy    # LiteLLM proxy service wrapper
└── run-litellm-local    # Local LiteLLM runner
```

## tests/

```
tests/
├── __init__.py          # Package marker
├── test_cli.py          # CLI command tests (entry point, env, profiles)
├── test_callbacks.py    # Provider compatibility callback tests
└── test_hooks.py        # Hook system tests
```

## playground/

Pre-configured directories for testing profile switching: `cerebras-project/`, `groq-project/`, `local-project/`, `multi-project/`. Each contains `.envrc`, `.envrc.user`, `.gitignore`.

## XDG Runtime Paths

| Type | Default Path |
|------|-------------|
| Config | `~/.config/run-claude/` (.secrets, .env, profiles, models, .initialized) |
| State | `~/.local/state/run-claude/` (state.json, proxy.pid, proxy.log, litellm_config.yaml) |

## Key Files Requiring Setup

| File | Action |
|------|--------|
| `~/.config/run-claude/.secrets` | Auto-created on first run; add API keys |
| `.envrc` | Run `direnv allow` in project root |
| Shell hooks | Run `hooks/install.sh` for auto-switching |
