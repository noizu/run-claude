# PRD-02: Containerized LiteLLM

**Phase**: 1B | **Est**: 3 days | **Repo**: run-claude

## Context

LiteLLM proxy currently runs as a local subprocess managed by `proxy.py` with PID files, signal handling, and a separate venv (`~/.local/share/litellm/.venv`). This is fragile: stale PID files, permission issues on log files, complex venv management. Moving to a Docker container alongside TimescaleDB simplifies lifecycle, eliminates venv management, and enables restart policies.

## Goals

1. Custom Dockerfile with litellm[proxy], prisma, and callbacks baked in
2. LiteLLM as a service in the same docker-compose as TimescaleDB
3. Move infrastructure config to `~/.config/run-claude/services/`
4. Rewrite `proxy.py` lifecycle to use `docker compose` instead of subprocess
5. Obviate the `scripts/run-litellm-proxy` venv setup

---

## 2a: Custom Dockerfile

### New File: `dep/litellm.Dockerfile`

```dockerfile
FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install LiteLLM + dependencies
RUN pip install --no-cache-dir \
    'litellm[proxy]' \
    litellm-proxy-extras \
    psycopg2-binary \
    'prisma==0.11.0' \
    prometheus_client \
    pyyaml

# Callbacks directory (mounted at runtime for dev, copied for prod)
COPY run_claude/callbacks/ /app/callbacks/

ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV STORE_MODEL_IN_DB="True"
ENV USE_PRISMA_MIGRATE="True"

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -sf http://localhost:4444/health || exit 1

EXPOSE 4444

ENTRYPOINT ["litellm"]
CMD ["--host", "0.0.0.0", "--port", "4444", "--config", "/app/config/litellm_config.yaml"]
```

### Build Context

The Dockerfile lives in `dep/` but build context is the project root (to COPY callbacks).

```bash
docker build -f dep/litellm.Dockerfile -t run-claude-litellm:latest .
```

---

## 2b: Updated docker-compose.yaml

### Modified File: `dep/docker-compose.yaml`

```yaml
version: "3.8"

services:
  timescaledb:
    image: timescale/timescaledb:2.23.1-pg17
    container_name: run-claude-timescaledb
    # ... existing config unchanged ...
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - internal

  litellm:
    build:
      context: ${RUN_CLAUDE_PROJECT_ROOT:-.}
      dockerfile: dep/litellm.Dockerfile
    image: run-claude-litellm:latest
    container_name: run-claude-litellm
    depends_on:
      timescaledb:
        condition: service_healthy
    env_file:
      - ${RUN_CLAUDE_CONFIG:-${HOME}/.config/run-claude}/.env
    environment:
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
      - DATABASE_URL=postgresql://postgres:${RUN_CLAUDE_TIMESCALEDB_PASSWORD}@timescaledb:5432/postgres
      - STORE_MODEL_IN_DB=True
      - USE_PRISMA_MIGRATE=True
    ports:
      - "${LITELLM_PORT:-4444}:4444"
    volumes:
      - ${RUN_CLAUDE_CONFIG:-${HOME}/.config/run-claude}/litellm_config.yaml:/app/config/litellm_config.yaml:ro
      - litellm-logs:/var/log
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:4444/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 90s
    networks:
      - internal

volumes:
  timescaledb-data:
  litellm-logs:

networks:
  internal:
    name: run-claude-network
    driver: bridge
```

**Key changes:**
- Internal network: litellm connects to `timescaledb:5432` (not `localhost:5433`)
- Config mounted from `~/.config/run-claude/litellm_config.yaml`
- Callbacks baked into image (can also mount for dev)
- `litellm-logs` volume for persistent logs
- Health check with 90s start_period (prisma migrations take time)

---

## 2c: Move Infrastructure to Config Directory

### Files to Modify

**`run_claude/proxy.py`**:

```python
def get_services_dir() -> Path:
    """Infrastructure config location (was get_dep_dir)."""
    return get_config_dir() / "services"

def get_litellm_config_path() -> Path:
    """LiteLLM config now lives in config dir."""
    return get_config_dir() / "litellm_config.yaml"
```

**`run_claude/proxy.py`** — `install_infrastructure()`:

Update target from `~/.local/state/run-claude/dep/` to `~/.config/run-claude/services/`.

**Auto-migration** in `ensure_initialized()`:

```python
old_dep = get_state_dir() / "dep"
new_services = get_services_dir()
if old_dep.exists() and not new_services.exists():
    shutil.move(str(old_dep), str(new_services))
    print(f"Migrated infrastructure: {old_dep} → {new_services}")
```

---

## 2d: Rewrite proxy.py Lifecycle

### Functions to Replace

**`start_proxy()`** — Replace subprocess.Popen with docker compose:

```python
def start_proxy(profile_name: str | None = None, no_db: bool = False, debug: bool = False) -> bool:
    services_dir = get_services_dir()
    config_path = get_litellm_config_path()

    # 1. Generate litellm_config.yaml (unchanged logic)
    generate_litellm_config(config_path, profile_name)

    # 2. Build image if needed
    subprocess.run(
        ["docker", "compose", "-f", str(services_dir / "docker-compose.yaml"),
         "--project-name", "run-claude",
         "build", "--quiet", "litellm"],
        check=True
    )

    # 3. Start services
    services = ["timescaledb", "litellm"] if not no_db else ["litellm"]
    subprocess.run(
        ["docker", "compose", "-f", str(services_dir / "docker-compose.yaml"),
         "--project-name", "run-claude",
         "--env-file", str(get_config_dir() / ".env"),
         "up", "-d"] + services,
        check=True
    )

    # 4. Wait for health
    return wait_for_container_healthy("run-claude-litellm", timeout=120)
```

**`stop_proxy()`** — Replace os.kill with docker compose stop:

```python
def stop_proxy(stop_db: bool = False) -> bool:
    services_dir = get_services_dir()
    services = ["litellm"]
    if stop_db:
        services.append("timescaledb")

    subprocess.run(
        ["docker", "compose", "-f", str(services_dir / "docker-compose.yaml"),
         "--project-name", "run-claude",
         "stop"] + services,
        check=True
    )
    return True
```

**`is_proxy_running()`** — Replace PID check with container status:

```python
def is_proxy_running() -> bool:
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", "run-claude-litellm"],
        capture_output=True, text=True
    )
    return result.returncode == 0 and result.stdout.strip() == "true"
```

**`health_check()`** — Keep HTTP-based, unchanged (still hits localhost:4444).

**New: `get_proxy_logs()`**:

```python
def get_proxy_logs(lines: int = 100) -> str:
    result = subprocess.run(
        ["docker", "logs", "--tail", str(lines), "run-claude-litellm"],
        capture_output=True, text=True
    )
    return result.stdout + result.stderr
```

### Remove

- PID file management (`proxy.pid` read/write/cleanup)
- `start_new_session=True` subprocess logic
- Log file fallback logic (`/var/log` → state dir)
- `get_proxy_pid()` (replace with container ID check)

---

## 2e: Simplify run-litellm-proxy

### Current Script (to deprecate): `scripts/run-litellm-proxy`

Replace with dev-only local runner:

### New File: `scripts/run-litellm-local`

```bash
#!/usr/bin/env bash
# Development only: run LiteLLM locally (not in container)
set -euo pipefail

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/run-claude"

# Load env
set -a
source "$CONFIG_DIR/.env"
set +a

echo "Starting LiteLLM locally (dev mode)..."
echo "Config: $CONFIG_DIR/litellm_config.yaml"

exec uvx --with 'litellm[proxy]' --with psycopg2-binary \
    litellm --host 127.0.0.1 --port 4444 \
    --config "$CONFIG_DIR/litellm_config.yaml"
```

Remove or deprecate `scripts/run-litellm-proxy` with a notice pointing to container mode.

---

## Testing

### Unit Tests

```python
class TestContainerLifecycle:
    @patch("subprocess.run")
    def test_start_proxy_calls_docker_compose_up(self, mock_run):
        start_proxy()
        calls = [c.args[0] for c in mock_run.call_args_list]
        assert any("up" in c and "-d" in c for c in calls)

    @patch("subprocess.run")
    def test_stop_proxy_calls_docker_compose_stop(self, mock_run):
        stop_proxy()
        calls = [c.args[0] for c in mock_run.call_args_list]
        assert any("stop" in c for c in calls)

    @patch("subprocess.run")
    def test_is_proxy_running_checks_container(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="true\n")
        assert is_proxy_running() is True
```

### Integration Tests

```bash
# Full lifecycle test
run-claude proxy start
docker ps | grep run-claude-litellm  # should be running
docker ps | grep run-claude-timescaledb  # should be running
curl -s http://localhost:4444/health  # should return healthy
run-claude proxy stop
docker ps | grep run-claude-litellm  # should not be running
```

### Migration Test

```bash
# Test auto-migration from old path
mkdir -p ~/.local/state/run-claude/dep
cp dep/docker-compose.yaml ~/.local/state/run-claude/dep/
run-claude proxy start  # should migrate and work
ls ~/.config/run-claude/services/docker-compose.yaml  # should exist
ls ~/.local/state/run-claude/dep  # should not exist
```

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Docker not installed | Detect early in `start_proxy()`, print install instructions |
| Port 4444 already in use | Parse docker error, suggest `LITELLM_PORT=4445` |
| Slow image build on first run | Pre-build in `run-claude install`, show progress |
| Container can't reach timescaledb | Internal network ensures DNS resolution |
| Callbacks not found in container | COPY in Dockerfile + volume mount fallback |
| Prisma migrations slow startup | 90s `start_period` in healthcheck |
