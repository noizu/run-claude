"""
LiteLLM proxy lifecycle management.

Handles starting, stopping, health checks, and model management via API.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

from .state import get_state_dir, load_state, save_state


DEFAULT_PROXY_HOST = "127.0.0.1"
DEFAULT_PROXY_PORT = 4444
DEFAULT_PROXY_URL = f"http://{DEFAULT_PROXY_HOST}:{DEFAULT_PROXY_PORT}"
DEFAULT_API_KEY = "sk-litellm-proxy"

HEALTH_CHECK_TIMEOUT = 60.0
HEALTH_CHECK_RETRIES = 30
HEALTH_CHECK_INTERVAL = 10.0


def get_proxy_url() -> str:
    """Get proxy URL from environment or default."""
    return os.environ.get("LITELLM_PROXY_URL", DEFAULT_PROXY_URL)


def get_api_key() -> str:
    """Get proxy API key from environment or default."""
    return os.environ.get("LITELLM_API_KEY", DEFAULT_API_KEY)


def get_pid_file() -> Path:
    """Get PID file path."""
    return get_state_dir() / "proxy.pid"


def get_log_file() -> Path:
    """Get log file path."""
    return get_state_dir() / "proxy.log"


def get_config_file() -> Path:
    """Get generated LiteLLM config file path."""
    return get_state_dir() / "litellm_config.yaml"


def _require_httpx() -> None:
    """Raise error if httpx not installed."""
    if httpx is None:
        raise RuntimeError(
            "httpx is required for proxy management.\n"
            "Install with: pip install httpx"
        )


def _require_yaml() -> None:
    """Raise error if PyYAML not installed."""
    if yaml is None:
        raise RuntimeError(
            "PyYAML is required for config generation.\n"
            "Install with: pip install pyyaml"
        )


@dataclass
class ProxyStatus:
    """Proxy status information."""
    running: bool
    pid: int | None = None
    healthy: bool = False
    url: str = DEFAULT_PROXY_URL
    model_count: int = 0
    db_healthy: bool = False


def generate_litellm_config(model_defs: list[dict[str, Any]] | None = None) -> Path:
    """
    Generate LiteLLM proxy config file with required settings.

    Args:
        model_defs: Optional list of model definitions to include.
                   If None, loads all available models.

    Returns:
        Path to the generated config file.
    """
    _require_yaml()

    # Import here to avoid circular imports
    from .profiles import load_model_definitions
    from .config import load_secrets

    # Load secrets from config file
    try:
        secrets = load_secrets(debug=False)
        env_vars = secrets.to_env()
        # Update environment with loaded secrets
        for key, value in env_vars.items():
            if key not in os.environ:
                os.environ[key] = value
    except Exception as e:
        # Secrets file may not exist or be empty, continue with existing env vars
        if "--debug" in sys.argv or "-d" in sys.argv:
            print(f"Warning: Could not load secrets: {e}", file=sys.stderr)

    # Build model list
    if model_defs is None:
        # Load all available models
        models = load_model_definitions()
        model_list = [m.to_dict() for m in models.values()]
    else:
        model_list = model_defs

    # Get database URL from environment or use default
    # Format: postgresql://user:password@host:port/database
    db_url = os.environ.get(
        "LITELLM_DATABASE_URL",
        "postgresql://postgres:${RUN_CLAUDE_TIMESCALEDB_PASSWORD}@localhost:5433/postgres"
    )

    # Expand environment variables in database URL
    if "${" in db_url and "}" in db_url:
        import re
        def expand_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))
        db_url = re.sub(r'\$\{([^}]+)\}', expand_var, db_url)

    print(f"Database connection string: {db_url}", file=sys.stderr)

    # Build config with required LiteLLM settings
    config = {
        "litellm_settings": {
            "drop_params": True,
            "forward_client_headers_to_llm_api": False,
        },
        "general_settings": {
            "master_key": "os.environ/LITELLM_MASTER_KEY",
            "database_url": db_url,
        },
        "model_list": model_list,
    }

    # Write config file
    config_path = get_config_file()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.dump(config, default_flow_style=False), encoding="utf-8")
    print(config_path)
    return config_path


def health_check(timeout: float = HEALTH_CHECK_TIMEOUT, wait_for_recovery: bool = False, max_retries: int = 0) -> bool:
    """
    Check if proxy is healthy.

    Args:
        timeout: Timeout for health check request
        wait_for_recovery: If True, wait for proxy to recover before returning
        max_retries: Max retries when wait_for_recovery=True (0 = infinite)

    Returns:
        True if proxy is healthy
    """
    if httpx is None:
        print("HTTPX REQUIRED")
        return False

    url = get_proxy_url()
    retry_count = 0

    while True:
        try:
            print(f"[GET] {url}/health")
            resp = httpx.get(f"{url}/health", timeout=timeout)
            print(resp)
            if resp.status_code == 200:
                return True

            # Not healthy yet
            if not wait_for_recovery:
                return False

            # Wait and retry if recovery mode enabled
            if max_retries > 0 and retry_count >= max_retries:
                return False

            retry_count += 1
            time.sleep(HEALTH_CHECK_INTERVAL)

        except Exception as e:
            print(f"Health check failed: {e}")

            if not wait_for_recovery:
                return False

            # Wait and retry if recovery mode enabled
            if max_retries > 0 and retry_count >= max_retries:
                return False

            retry_count += 1
            time.sleep(HEALTH_CHECK_INTERVAL)


def is_proxy_running() -> bool:
    """Check if proxy process is running."""
    pid_file = get_pid_file()
    if not pid_file.exists():
        return False

    try:
        pid = int(pid_file.read_text().strip())
        # Check if process exists
        os.kill(pid, 0)
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        # PID file stale, clean up
        pid_file.unlink(missing_ok=True)
        return False


def get_proxy_pid() -> int | None:
    """Get proxy PID if running."""
    pid_file = get_pid_file()
    if not pid_file.exists():
        return None

    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, 0)  # Check if process exists
        return pid
    except (ValueError, ProcessLookupError, PermissionError):
        return None


def start_proxy(config_path: str | None = None, wait: bool = True, empty_config: bool = False) -> bool:
    """
    Start LiteLLM proxy.

    Args:
        config_path: Path to LiteLLM config file. If None, generates one.
        wait: Wait for proxy to become healthy
        empty_config: If True, generate config with empty model list.
                     Models are loaded on-demand via ensure_models().

    Returns:
        True if proxy started successfully
    """
    if is_proxy_running() and health_check():
        return True

    state_dir = get_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)

    pid_file = get_pid_file()
    log_file = get_log_file()

    # Generate config if not provided
    if config_path is None:
        # Use empty model list if empty_config=True (for startup)
        # Otherwise load all models (for restart operations)
        model_defs = [] if empty_config else None
        config_path = str(generate_litellm_config(model_defs=model_defs))

    # Build command
    cmd = ["litellm", "--host", DEFAULT_PROXY_HOST, "--port", str(DEFAULT_PROXY_PORT)]
    cmd.extend(["--config", config_path])

    # Start proxy in background
    try:
        # Prepare environment for proxy
        env = os.environ.copy()
        env["STORE_MODEL_IN_DB"] = "True"

        with open(log_file, "a") as log:
            proc = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=log,
                start_new_session=True,
                env=env,
            )
    except (FileNotFoundError, PermissionError) as e:
        # litellm not installed or not accessible
        return False

    # Write PID file
    pid_file.write_text(str(proc.pid))

    # Update state
    state = load_state()
    state.proxy_pid = proc.pid
    save_state(state)

    if wait:
        # Wait for proxy to become healthy
        for _ in range(HEALTH_CHECK_RETRIES):
            if health_check():
                return True
            time.sleep(HEALTH_CHECK_INTERVAL)

        # Proxy didn't become healthy
        return False

    return True


def stop_proxy() -> bool:
    """
    Stop the proxy.

    Returns:
        True if proxy was stopped successfully
        False if process couldn't be stopped
    """
    pid = get_proxy_pid()

    if pid is None:
        # No PID file, check if process is running by command
        try:
            result = subprocess.run(
                ["pgrep", "-f", "litellm.*--host.*--port"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # Found running litellm process
                pids = result.stdout.strip().split("\n")
                print(f"Found running proxy process(es). Run one of:", file=sys.stderr)
                for p in pids:
                    print(f"  kill {p}", file=sys.stderr)
                return False
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # pgrep not available or timeout, assume no process
            return True

    try:
        os.kill(pid, signal.SIGTERM)

        # Wait for process to exit
        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except ProcessLookupError:
                # Process exited successfully
                get_pid_file().unlink(missing_ok=True)
                state = load_state()
                state.proxy_pid = None
                save_state(state)
                return True

        # Process didn't exit, try SIGKILL
        print(f"Process {pid} didn't exit after SIGTERM, trying SIGKILL...", file=sys.stderr)
        os.kill(pid, signal.SIGKILL)
        time.sleep(0.5)

        try:
            os.kill(pid, 0)
            # Still running
            print(f"Failed to kill process {pid}", file=sys.stderr)
            return False
        except ProcessLookupError:
            # Finally killed
            get_pid_file().unlink(missing_ok=True)
            state = load_state()
            state.proxy_pid = None
            save_state(state)
            return True

    except ProcessLookupError:
        # Process already exited
        get_pid_file().unlink(missing_ok=True)
        state = load_state()
        state.proxy_pid = None
        save_state(state)
        return True
    except PermissionError:
        print(f"Permission denied stopping process {pid}", file=sys.stderr)
        return False


def get_status() -> ProxyStatus:
    """Get proxy status."""
    pid = get_proxy_pid()
    running = pid is not None
    healthy = health_check() if running else False

    model_count = 0
    if healthy:
        models = list_models()
        model_count = len(models)

    db_healthy = test_db_connection(debug=True)

    return ProxyStatus(
        running=running,
        pid=pid,
        healthy=healthy,
        url=get_proxy_url(),
        model_count=model_count,
        db_healthy=db_healthy,
    )


def list_models() -> list[dict[str, Any]]:
    """Get list of models registered with proxy."""
    if httpx is None:
        return []

    url = get_proxy_url()
    api_key = get_api_key()

    try:
        resp = httpx.get(
            f"{url}/model/info",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data", [])
    except Exception:
        pass

    return []


def get_model_ids() -> set[str]:
    """Get set of model names/IDs registered with proxy."""
    models = list_models()
    ids = set()
    for m in models:
        if "model_name" in m:
            ids.add(m["model_name"])
        if "model_info" in m and "id" in m["model_info"]:
            ids.add(m["model_info"]["id"])
    return ids


def add_model(model_def: dict[str, Any], debug: bool = False) -> bool:
    """
    Add a model to the proxy.

    Args:
        model_def: Model definition with model_name and litellm_params
        debug: If True, print debug info on failure

    Returns:
        True if model added successfully
    """
    if httpx is None:
        return False

    url = get_proxy_url()
    api_key = get_api_key()

    try:
        resp = httpx.post(
            f"{url}/model/new",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=model_def,
            timeout=10.0,
        )
        if resp.status_code in (200, 201):
            return True
        if debug:
            model_name = model_def.get("model_name", "unknown")
            print(f"Failed to add model '{model_name}': {resp.status_code} {resp.text}", file=sys.stderr)
        return False
    except Exception as e:
        if debug:
            model_name = model_def.get("model_name", "unknown")
            print(f"Failed to add model '{model_name}': {e}", file=sys.stderr)
        return False


def delete_model(model_id: str) -> bool:
    """
    Delete a model from the proxy.

    Args:
        model_id: Model ID to delete

    Returns:
        True if model deleted successfully
    """
    if httpx is None:
        return False

    url = get_proxy_url()
    api_key = get_api_key()

    try:
        resp = httpx.post(
            f"{url}/model/delete",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"id": model_id},
            timeout=10.0,
        )
        return resp.status_code in (200, 204)
    except Exception:
        return False


def ensure_models(model_defs: list[dict[str, Any]], debug: bool = False, wait_for_recovery: bool = False) -> tuple[int, int]:
    """
    Ensure models are registered with proxy.

    Args:
        model_defs: List of model definitions
        debug: If True, print debug info on failures
        wait_for_recovery: If True, wait for proxy to recover before returning

    Returns:
        Tuple of (added_count, skipped_count)
    """
    # If wait_for_recovery enabled, wait for proxy to become healthy
    if wait_for_recovery:
        health_check(wait_for_recovery=True, max_retries=HEALTH_CHECK_RETRIES)

    existing = get_model_ids()
    added = 0
    skipped = 0

    for model_def in model_defs:
        model_name = model_def.get("model_name", "")
        if model_name in existing:
            skipped += 1
            continue

        if add_model(model_def, debug=debug):
            added += 1
        # Failures are logged by add_model when debug=True

    return added, skipped


def regenerate_config_and_restart() -> bool:
    """
    Regenerate the LiteLLM config and restart the proxy.

    Useful when model definitions have been updated.
    """
    was_running = is_proxy_running()

    if was_running:
        stop_proxy()

    # Regenerate config
    config_path = generate_litellm_config()

    if was_running:
        return start_proxy(str(config_path))

    return True


def test_db_connection(debug: bool = False) -> bool:
    """
    Test database connectivity.

    Args:
        debug: If True, print debug info

    Returns:
        True if database connection successful
    """
    # Load secrets from config file
    try:
        from .config import load_secrets
        secrets = load_secrets(debug=False)
        env_vars = secrets.to_env()
        # Update environment with loaded secrets
        for key, value in env_vars.items():
            if key not in os.environ:
                os.environ[key] = value
    except Exception as e:
        # Secrets file may not exist or be empty, continue with existing env vars
        if debug:
            print(f"Warning: Could not load secrets: {e}", file=sys.stderr)

    # Get database URL from environment or use default
    db_url = os.environ.get(
        "LITELLM_DATABASE_URL",
        "postgresql://postgres:${RUN_CLAUDE_TIMESCALEDB_PASSWORD}@localhost:5433/postgres"
    )

    # Expand environment variables in database URL
    if "${" in db_url and "}" in db_url:
        import re
        def expand_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))
        db_url = re.sub(r'\$\{([^}]+)\}', expand_var, db_url)

    print(f"Database connection string (expanded): {db_url}", file=sys.stderr)

    try:
        import psycopg2
    except ImportError:
        if debug:
            print("psycopg2 is required for database testing.", file=sys.stderr)
            print("Install with: pip install psycopg2-binary", file=sys.stderr)
        return False

    # Parse connection string
    # Format: postgresql://user:password@host:port/database
    try:
        # Simple parser for postgresql URLs
        if not db_url.startswith("postgresql://"):
            if debug:
                print(f"Invalid database URL format: {db_url}", file=sys.stderr)
            return False

        # Remove scheme
        conn_str = db_url.replace("postgresql://", "")

        # Split credentials and host info
        if "@" not in conn_str:
            if debug:
                print("Invalid database URL: missing host", file=sys.stderr)
            return False

        creds, host_info = conn_str.split("@", 1)
        user, password = creds.split(":", 1) if ":" in creds else (creds, "")

        # Split host and port/database
        if "/" in host_info:
            host_port, database = host_info.split("/", 1)
        else:
            host_port = host_info
            database = "postgres"

        # Split host and port
        if ":" in host_port:
            host, port = host_port.split(":", 1)
            port = int(port)
        else:
            host = host_port
            port = 5432

        # Expand environment variables in password
        if password.startswith("${") and password.endswith("}"):
            env_var = password[2:-1]
            password = os.environ.get(env_var, "")

        if debug:
            print(f"Testing database connection to {host}:{port}/{database}...", file=sys.stderr)

        # Test connection
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=5,
        )
        conn.close()

        if debug:
            print(f"Database connection successful!", file=sys.stderr)
        return True

    except Exception as e:
        if debug:
            print(f"Database connection failed: {e}", file=sys.stderr)
        return False
