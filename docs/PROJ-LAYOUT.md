# Project Layout

This document describes the folder structure and file organization of the run-claude project.

## Overview

**run-claude** is an agent shim controller that enables directory-aware model routing via LiteLLM proxy. It turns folder context into live inference overrides, allowing users to switch between different AI model providers based on their current directory.

## Root Level

```
/github/infra/run-claude/
├── docs/                    # Documentation
├── dep/                     # Infrastructure dependencies (Docker)
├── hooks/                   # Shell integration hooks
├── playground/              # Test directories for validation
├── run_claude/              # Main Python package
├── templates/               # Template files for direnv
├── tests/                   # Test suite
├── Makefile                 # Build automation
├── profiles.yaml            # Profile definitions
├── pyproject.toml           # Python project configuration
├── uv.lock                  # Dependency lockfile
├── README.md                # User guide
├── SECRETS.md               # Secrets configuration guide
├── SECRETS_ADVANCED.md      # Advanced secrets management
├── SECRETS_QUICKSTART.md    # Quick reference for secrets
└── with-agent-shim          # Wrapper script for running with profiles
```

## `/run_claude` - Main Package

The core Python package implementing the agent shim controller.

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | ~8 | Package initialization, version declaration |
| `cli.py` | ~766 | Command-line interface and command dispatch |
| `config.py` | ~322 | Secrets management and configuration loading |
| `models.yaml` | ~450 | Built-in LiteLLM model definitions |
| `profiles.py` | ~674 | Profile loading and management system |
| `proxy.py` | ~866 | LiteLLM proxy lifecycle management |
| `state.py` | ~177 | Persistent state management (tokens, refcounts) |

### Key Module Responsibilities

- **cli.py**: Entry point with commands: `enter`, `leave`, `janitor`, `set-folder`, `status`, `env`, `proxy`, `profiles`, `models`, `install`, `secrets`, `with`
- **profiles.py**: Multi-file profile loading with fallthrough, model resolution
- **proxy.py**: LiteLLM proxy start/stop, health checks, model registration via API
- **state.py**: Token tracking, model refcounting, lease scheduling (delayed deletion)
- **config.py**: Secrets file loading, template generation, `.env` export

## `/dep` - Infrastructure Dependencies

Docker Compose configuration for containerized services.

```
dep/
├── docker-compose.yaml           # Main TimescaleDB service definition
├── docker-compose.override.yaml  # Development overrides (port 5433)
└── config/
    └── timescaledb/
        └── init-databases.sql    # Database initialization (vector, pg_trgm extensions)
```

### Services

- **TimescaleDB**: `timescale/timescaledb:2.23.1-pg17`
  - Container: `run-claude-timescaledb`
  - Volume: `timescaledb-data` (persistent)
  - Network: `run-claude-network` (bridge)
  - Dev port: `5433:5432`

### Environment Files

The compose file loads secrets from:
1. `$RUN_CLAUDE_HOME/.env`
2. `$XDG_CONFIG_HOME/run-claude/.env`
3. `~/.config/run-claude/.env` (default)

## `/templates` - Environment Templates

Template files for direnv configuration.

```
templates/
├── envrc.tmpl       # Template for .envrc (auto-generated)
└── envrc.user.tmpl  # Template for .envrc.user (user-editable)
```

### Placeholder Substitution

- `{{TOKEN}}`: Replaced with SHA256 hash of directory path (16 hex chars)
- `{{PROFILE}}`: Replaced with selected profile name

## `/hooks` - Shell Integration

Shell hooks for automatic profile switching via PROMPT_COMMAND/precmd.

```
hooks/
├── bash_hook.sh   # Bash prompt hook (PROMPT_COMMAND)
├── zsh_hook.zsh   # Zsh precmd hook
└── install.sh     # Hook installation script
```

### Hook Behavior

1. Detect `AGENT_SHIM_TOKEN` changes (set by direnv)
2. Call `run-claude enter` when entering shimmed directory
3. Call `run-claude leave` when leaving
4. Run janitor periodically for cleanup

## `/playground` - Test Directories

Pre-configured directories for testing profile switching.

```
playground/
├── README.md              # Testing documentation
├── test-switching.sh      # Automated test script
├── cerebras-project/      # Cerebras profile test dir
├── groq-project/          # Groq profile test dir
├── local-project/         # Local (Ollama) profile test dir
└── multi-project/         # Multi-provider test dir
```

Each project contains:
- `.envrc`: Sets `AGENT_SHIM_TOKEN`, sources user config
- `.envrc.user`: Sets `AGENT_SHIM_PROFILE`
- `.gitignore`: Excludes envrc files

## `/tests` - Test Suite

```
tests/
├── __init__.py     # Package marker
└── test_cli.py     # CLI command tests
```

### Test Coverage

- `TestMain`: Entry point tests
- `TestEnvCommand`: Environment variable output tests
- `TestProfilesCommand`: Profile management tests

## Configuration Files

### `profiles.yaml` (Root)

Main profile configuration defining 14+ built-in profiles:

- **anthropic**: Native Claude models
- **openai**: GPT models
- **cerebras**, **cerebras2**, **cerebras-pro**: Fast inference
- **groq**, **groq2**: Ultra-fast inference
- **gemini**: Google Gemini
- **azure**: Azure OpenAI
- **grok**: xAI Grok
- **deepseek**: DeepSeek models
- **mistral**: Mistral AI
- **perplexity**: Search-augmented
- **local**: Ollama/vLLM

### `pyproject.toml`

Python project metadata:
- Version: 0.1.2
- Entry point: `run_claude.cli:main`
- Dependencies: pyyaml, httpx, prisma, psycopg2-binary

### `Makefile`

Build targets:
- `test`: Run pytest
- `test-cov`: Run with coverage
- `coverage-html`: Generate HTML report
- `install`: Install via uv
- `refresh`: Force reinstall

## XDG-Compliant Paths

The project follows XDG Base Directory Specification:

| Type | Default Path | Env Override |
|------|--------------|--------------|
| Config | `~/.config/run-claude/` | `XDG_CONFIG_HOME` |
| State | `~/.local/state/run-claude/` | `XDG_STATE_HOME` |

### Config Directory Contents

```
~/.config/run-claude/
├── .secrets            # API keys and passwords (YAML)
├── .env                # Exported secrets for Docker
├── .initialized        # First-run marker
├── profiles.yaml       # User profiles
├── user.profiles.yaml  # User override profiles
└── models.yaml         # User model definitions
```

### State Directory Contents

```
~/.local/state/run-claude/
├── state.json          # Application state (tokens, refcounts)
├── proxy.pid           # Running proxy PID
├── proxy.log           # Proxy output log
└── litellm_config.yaml # Generated LiteLLM configuration
```

## Generated Files

Files created by `run-claude set-folder <profile>`:

```
<project>/
├── .envrc              # Auto-generated direnv config
├── .envrc.user         # User-editable profile selection
└── .gitignore          # Updated to exclude .envrc.user
```
