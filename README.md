# run-claude - Agent Shim Controller for Claude

Directory-aware model routing via LiteLLM proxy.

## Overview

`run-claude` turns folder context into live inference overrides. When you `cd` into a directory that declares an agent shim profile, the directory's required models get added to a running LiteLLM proxy, and environment variables are set so your tools (Claude Code, etc.) route through the proxy.

## Requirements

- **Python** >= 3.10
- **uv** — Python package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Docker** — for TimescaleDB and LiteLLM proxy containers
- **direnv** — for automatic environment switching per directory

## Installation

```bash
# 1. Clone and install
git clone <repo-url> && cd run-claude
make install          # installs via uv tool install

# 2. Run the interactive setup wizard
run-claude setup
```

The setup wizard will:
- Ask for your API keys (Anthropic, OpenAI, Cerebras, Groq, etc.)
- Auto-generate infrastructure credentials (database password, proxy master key)
- Write `~/.config/run-claude/.secrets` and export `.env` for Docker

```bash
# 3. Start the proxy
run-claude proxy start

# 4. Install shell hooks for automatic profile switching
./hooks/install.sh
```

### Supported Providers

The wizard can configure keys for any of these providers:

| Provider | Env Variable | Profiles |
|----------|-------------|----------|
| Anthropic | `ANTHROPIC_API_KEY` | `anthropic` |
| OpenAI | `OPENAI_API_KEY` | `openai` |
| Google Gemini | `GEMINI_API_KEY` | `gemini` |
| Cerebras | `CEREBRAS_API_KEY` | `cerebras`, `cerebras2` |
| Cerebras Pro | `CEREBRAS_SUB_KEY` | `cerebras-pro` |
| Z.AI | `ZAI_API_KEY` | `zai-pro` |
| Z.AI Pro | `ZAI_SUB_KEY` | `zai-pro` (subscription) |
| Groq | `GROQ_API_KEY` | `groq`, `groq2`, `groq-pro`, `groq-mix` |
| xAI Grok | `GROK_API_KEY` | `grok` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek` |
| Mistral | `MISTRAL_API_KEY` | `mistral` |
| Perplexity | `PERPLEXITY_API_KEY` | `perplexity` |

To add or change keys later: `run-claude setup --reconfigure`

## Quick Start

```bash
# Configure a folder with a profile
cd /path/to/my/project
run-claude set-folder cerebras
direnv allow

# The folder now uses the Cerebras profile when you enter it.
# Or run a one-off command with a profile:
run-claude with cerebras -- claude
```

## Commands

### Setup & Configuration

```bash
run-claude setup                  # Interactive setup wizard
run-claude setup -r               # Reconfigure existing setup
run-claude secrets init           # Initialize secrets template (non-interactive)
run-claude secrets path           # Show secrets file location
run-claude secrets export         # Export secrets to .env for Docker
```

### Directory Management

```bash
run-claude set-folder <profile>   # Configure current directory
run-claude enter <token> <profile> # Activate a profile (used by shell hook)
run-claude leave <token>          # Deactivate a profile (used by shell hook)
run-claude janitor                # Clean up expired model leases
```

### Status & Environment

```bash
run-claude status                 # Show current state
run-claude env <profile>          # Print environment variables
run-claude env <profile> --export # Print export statements
```

### Proxy Management

```bash
run-claude proxy start            # Start LiteLLM proxy
run-claude proxy stop             # Stop proxy
run-claude proxy status           # Show proxy status
run-claude proxy health           # Health check
```

### Database Management

```bash
run-claude db start               # Start TimescaleDB container
run-claude db stop                # Stop container (--remove for volumes)
run-claude db status              # Container status
run-claude db migrate             # Run prisma migrate
```

### Profile & Model Management

```bash
run-claude profiles list          # List available profiles
run-claude profiles show <name>   # Show profile details
run-claude models list            # List available model definitions
run-claude models show <name>     # Show model definition details
```

## Architecture

Two-layer configuration:

1. **Model Definitions** (`models.yaml`) — standalone LiteLLM model configs
2. **Profiles** (`profiles.yaml`) — lightweight references mapping opus/sonnet/haiku tiers

For detailed architecture, see [docs/PROJ-ARCH.md](docs/PROJ-ARCH.md).

## How It Works

1. **Shell hook** detects when `AGENT_SHIM_TOKEN` changes (set by direnv)
2. **run-claude enter** registers models with the LiteLLM proxy
3. **Environment variables** are set to route traffic through the proxy
4. **run-claude leave** decrements refcounts when you leave the directory
5. **run-claude janitor** cleans up unused models after 15 minutes

## File Locations

| Type | Path |
|------|------|
| Secrets | `~/.config/run-claude/.secrets` |
| Env file | `~/.config/run-claude/.env` |
| User profiles | `~/.config/run-claude/profiles.yaml` |
| User models | `~/.config/run-claude/models.yaml` |
| State | `~/.local/state/run-claude/state.json` |
| Proxy PID | `~/.local/state/run-claude/proxy.pid` |
| Proxy log | `~/.local/state/run-claude/proxy.log` |
| LiteLLM config | `~/.local/state/run-claude/litellm_config.yaml` |

## Development

```bash
make dev              # Install dev dependencies
make test             # Run tests
make test-cov         # Run with coverage
make refresh          # Force reinstall
```

For secrets management details, see [SECRETS.md](SECRETS.md).
