# Project Architecture

This document describes the architecture, data flow, and design patterns of the run-claude project.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLI Layer (cli.py)                          │
│   Main entry point with command dispatch for enter/leave/proxy      │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐       ┌───────────────┐
│   Profiles    │      │     State     │       │     Proxy     │
│  Management   │      │  Management   │       │  Management   │
│ (profiles.py) │      │  (state.py)   │       │  (proxy.py)   │
└───────┬───────┘      └───────┬───────┘       └───────┬───────┘
        │                      │                       │
        ▼                      ▼                       ▼
┌───────────────┐      ┌───────────────┐       ┌───────────────┐
│  YAML Files   │      │  state.json   │       │ LiteLLM Proxy │
│profiles.yaml  │      │               │       │   (port 4444) │
│ models.yaml   │      │               │       │               │
└───────────────┘      └───────────────┘       └───────┬───────┘
                                                       │
                                               ┌───────▼───────┐
                                               │  TimescaleDB  │
                                               │  (port 5433)  │
                                               └───────────────┘
```

## Core Components

### 1. CLI Layer (`cli.py`)

Entry point handling all user commands.

**Commands:**

| Command | Handler | Purpose |
|---------|---------|---------|
| `enter` | `cmd_enter()` | Register directory + profile + token |
| `leave` | `cmd_leave()` | Unregister directory token |
| `janitor` | `cmd_janitor()` | Clean up expired model leases |
| `set-folder` | `cmd_set_folder()` | Configure directory with .envrc |
| `status` | `cmd_status()` | Show proxy & state status |
| `env` | `cmd_env()` | Print environment for profile |
| `proxy` | `cmd_proxy()` | Proxy control (start/stop/status) |
| `profiles` | `cmd_profiles()` | Profile management |
| `models` | `cmd_models()` | Model definition management |
| `with` | `cmd_run()` | Run command with profile |
| `install` | `cmd_install()` | Install built-in assets |
| `secrets` | `cmd_secrets()` | Secrets management |

### 2. Profile System (`profiles.py`)

Multi-file configuration with fallthrough loading.

**Data Structures:**

```python
@dataclass
class ModelDef:
    model_name: str
    litellm_params: dict[str, Any]

@dataclass
class ProfileMeta:
    name: str
    opus_model: str      # Model name for Opus tier
    sonnet_model: str    # Model name for Sonnet tier
    haiku_model: str     # Model name for Haiku tier

@dataclass
class Profile:
    meta: ProfileMeta
    model_list: list[ModelDef]
    source_path: Path | None
```

**File Search Order (first match wins):**

1. `~/.config/run-claude/user.profiles.yaml` (highest priority)
2. `~/.config/run-claude/profiles.yaml`
3. `<package>/user.profiles.yaml`
4. `<package>/profiles.yaml` (lowest priority)

**Key Functions:**

- `load_profile(name)`: Load profile with fallthrough
- `resolve_profile_models()`: Convert model names to ModelDef objects
- `hydrate_model_def()`: Expand `os.environ/VAR` references
- `list_profiles()`: List available profiles

### 3. State Management (`state.py`)

Persistent state tracking using JSON.

**Data Structures:**

```python
@dataclass
class TokenInfo:
    profile: str
    last_seen: float  # Unix timestamp
    directory: str

@dataclass
class State:
    proxy_pid: int | None
    active_tokens: dict[str, TokenInfo]
    model_refcounts: dict[str, int]
    model_leases: dict[str, float]  # model -> delete_after epoch
    last_janitor_run: float
```

**Storage:** `~/.local/state/run-claude/state.json`

### 4. Proxy Management (`proxy.py`)

LiteLLM proxy lifecycle and model registration.

**Configuration:**

| Setting | Default |
|---------|---------|
| Host | `127.0.0.1` |
| Port | `4444` |
| Master Key | `sk-litellm-master-key-12345` |
| Database | `postgresql://localhost:5433/postgres` |

**Key Functions:**

- `start_proxy()`: Spawn proxy subprocess, wait for health
- `stop_proxy()`: Graceful shutdown with SIGTERM/SIGKILL
- `health_check()`: GET `/health` endpoint
- `add_model()`: POST `/model/new`
- `delete_model()`: POST `/model/delete`
- `ensure_models()`: Bulk add models (skip existing)

### 5. Secrets Management (`config.py`)

Secure credential storage and export.

**File Location:** `~/.config/run-claude/.secrets` (YAML, mode 0600)

**Required Secrets:**

- `RUN_CLAUDE_TIMESCALEDB_PASSWORD`
- `ANTHROPIC_API_KEY`

**Key Functions:**

- `load_secrets()`: Load YAML secrets file
- `create_secrets_template()`: Generate documented template
- `export_env_file()`: Convert to `.env` for Docker

## Data Flows

### Directory Enter Flow

```
User enters directory (via direnv)
        │
        ▼
┌───────────────────────────────────────────┐
│ .envrc sets AGENT_SHIM_TOKEN              │
│ .envrc.user sets AGENT_SHIM_PROFILE       │
│ .envrc evals: run-claude env $PROFILE     │
└───────────────────┬───────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────┐
│ Shell hook detects token change           │
│ Calls: run-claude enter $TOKEN $PROFILE   │
└───────────────────┬───────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────┐
│ cli.cmd_enter():                          │
│   1. Load profile by name                 │
│   2. Resolve model definitions            │
│   3. Ensure proxy running                 │
│   4. Register models with proxy           │
│   5. Add token to state                   │
│   6. Increment model refcounts            │
│   7. Save state                           │
└───────────────────────────────────────────┘
```

### Directory Leave Flow

```
User leaves directory
        │
        ▼
┌───────────────────────────────────────────┐
│ Shell hook detects token cleared          │
│ Calls: run-claude leave $TOKEN            │
└───────────────────┬───────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────┐
│ cli.cmd_leave():                          │
│   1. Load state                           │
│   2. Get token info (profile, models)     │
│   3. Decrement model refcounts            │
│   4. If refcount=0: set lease (15 min)    │
│   5. Remove token from state              │
│   6. Save state                           │
└───────────────────────────────────────────┘
```

### Janitor Cleanup Flow

```
Periodic janitor run (rate-limited to 1/minute)
        │
        ▼
┌───────────────────────────────────────────┐
│ cli.cmd_janitor():                        │
│   1. Load state                           │
│   2. Get expired leases                   │
│   3. For each expired model:              │
│      - Delete from proxy                  │
│      - Clear lease from state             │
│   4. Save state                           │
└───────────────────────────────────────────┘
```

### Profile Resolution Flow

```
profiles.load_profile("anthropic")
        │
        ▼
┌───────────────────────────────────────────┐
│ Search profile files in priority order    │
│ (user override → user → built-in)         │
└───────────────────┬───────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────┐
│ Check if profile disabled (model: null)   │
│ If disabled, continue to next file        │
└───────────────────┬───────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────┐
│ Extract ProfileMeta:                      │
│   - opus_model: "claude-opus-4-..."       │
│   - sonnet_model: "claude-sonnet-4-..."   │
│   - haiku_model: "claude-3-5-haiku-..."   │
└───────────────────┬───────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────┐
│ resolve_profile_models():                 │
│   1. Load model definitions               │
│   2. For each model name in profile:      │
│      - Find ModelDef by name              │
│      - hydrate_model_def() (expand env)   │
│   3. Return list[ModelDef]                │
└───────────────────────────────────────────┘
```

## Design Patterns

### 1. Stable Token Generation

Directory paths are hashed to create stable, reproducible tokens:

```python
canonical = directory.resolve()
token = hashlib.sha256(str(canonical).encode()).hexdigest()[:16]
```

### 2. Refcount with Lease Pattern

Prevents model thrashing (rapid add/delete cycles):

```
Refcount > 0  →  Model is in-use, keep registered
Refcount = 0  →  Model enters lease period (15 min default)
Lease expired →  Janitor deletes from proxy
```

### 3. Environment Variable Hydration

Model definitions reference environment variables with special syntax:

```yaml
litellm_params:
  api_key: os.environ/ANTHROPIC_API_KEY
```

Expanded at runtime before registering with proxy.

### 4. Multi-File Configuration Fallback

Profiles and models use layered configuration:

- **User files** override built-in files
- **Disabled profiles** (`model: null`) fall through to next source
- Enables customization without modifying source

### 5. First-Run Initialization

```python
ensure_initialized()
  → Check ~/.initialized marker
  → If missing: copy built-in profiles/models to user config
  → Create XDG-compliant directories
```

### 6. Health Check with Recovery

```python
health_check(wait_for_recovery=True, max_retries=30)
  → Retry up to 30 times with 10s interval
  → Allows proxy to stabilize after model registration
```

## External Dependencies

| Package | Purpose |
|---------|---------|
| `pyyaml` | YAML parsing for profiles, models, secrets |
| `httpx` | HTTP client for proxy API calls |
| `psycopg2-binary` | PostgreSQL driver for database testing |
| `prisma` | ORM for LiteLLM proxy (referenced in env) |

## Environment Variables

### Proxy Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `LITELLM_PROXY_URL` | `http://127.0.0.1:4444` | Proxy base URL |
| `LITELLM_MASTER_KEY` | `sk-litellm-master-key-12345` | Proxy API key |
| `LITELLM_DATABASE_URL` | See below | Database connection |
| `STORE_MODEL_IN_DB` | `True` | Enable DB model storage |
| `USE_PRISMA_MIGRATE` | `True` | Enable migrations |

### Client Environment (exported by `run-claude env`)

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_AUTH_TOKEN` | Proxy master key |
| `ANTHROPIC_BASE_URL` | Proxy URL |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Profile's opus model |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Profile's sonnet model |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Profile's haiku model |
| `API_TIMEOUT_MS` | API timeout (3000000ms) |

## Database Schema

TimescaleDB with extensions:

- **vector**: Vector embeddings for LLM context
- **pg_trgm**: Trigram search for text matching

LiteLLM uses Prisma ORM for:

- Model registry and parameters
- API key management
- Request/response logging

## Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Host Machine                            │
│                                                             │
│  ┌─────────────┐                    ┌─────────────────────┐ │
│  │   Claude    │ ──HTTP:4444──────► │   LiteLLM Proxy     │ │
│  │   Client    │                    │   (port 4444)       │ │
│  └─────────────┘                    └──────────┬──────────┘ │
│                                                │            │
│                                     TCP:5433   │            │
│                                                ▼            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Docker: run-claude-network                 ││
│  │  ┌───────────────────────────────────────────────────┐  ││
│  │  │           TimescaleDB Container                    │  ││
│  │  │           (internal port 5432)                     │  ││
│  │  │           Volume: timescaledb-data                 │  ││
│  │  └───────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Process Lifecycle

### Proxy Startup

1. Generate `litellm_config.yaml` with model definitions
2. Spawn `litellm --config <path>` subprocess
3. Wait for health check (30 retries × 10s)
4. Store PID in `~/.local/state/run-claude/proxy.pid`
5. Update state with `proxy_pid`

### Proxy Shutdown

1. Read PID from file
2. Send SIGTERM
3. Wait for graceful exit (timeout: 5s)
4. Send SIGKILL if needed
5. Clean up PID file
6. Update state

## Security Considerations

- Secrets file uses mode `0600` (owner only)
- API keys stored in `~/.config/run-claude/.secrets`
- Environment variables hydrated at runtime (not stored in configs)
- Proxy runs on localhost only (`127.0.0.1`)
- Database on non-standard port (`5433`) to avoid conflicts
