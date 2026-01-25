"""
LiteLLM proxy lifecycle management.

Handles starting, stopping, health checks, and model management via API.
"""

from __future__ import annotations

import json
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
DEFAULT_MASTER_KEY = "sk-litellm-master-key-12345"
DEFAULT_LITELLM_COMMAND = "litellm"

HEALTH_CHECK_TIMEOUT = 60.0
HEALTH_CHECK_RETRIES = 30
HEALTH_CHECK_INTERVAL = 10.0


def get_proxy_url() -> str:
    """Get proxy URL from environment or default."""
    return os.environ.get("LITELLM_PROXY_URL", DEFAULT_PROXY_URL)


def get_master_key() -> str:
    """Get proxy master key from environment or default."""
    return os.environ.get("LITELLM_MASTER_KEY", DEFAULT_MASTER_KEY)


def get_api_key() -> str:
    """Get API key for proxy authentication."""
    return get_master_key()


def get_litellm_command() -> str:
    """Get litellm command from environment or default.

    On NixOS systems, use LITELLM_COMMAND=litellm-proxy to specify the uv alias.
    """
    return os.environ.get("LITELLM_COMMAND", DEFAULT_LITELLM_COMMAND)


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


def _hydrate_model_dict(model_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Hydrate a model definition dict by expanding environment variable references.

    Replaces values like 'os.environ/VAR_NAME' with the actual environment variable value.

    Args:
        model_dict: Model definition dict to hydrate

    Returns:
        New dict with hydrated litellm_params
    """
    hydrated = model_dict.copy()
    litellm_params = hydrated.get("litellm_params", {})

    if not isinstance(litellm_params, dict):
        return hydrated

    hydrated_params = {}
    for key, value in litellm_params.items():
        if isinstance(value, str) and value.startswith("os.environ/"):
            # Extract environment variable name
            env_var = value.replace("os.environ/", "")
            hydrated_value = os.environ.get(env_var)
            if hydrated_value:
                hydrated_params[key] = hydrated_value
            else:
                # Keep original if env var not found
                hydrated_params[key] = value
        else:
            hydrated_params[key] = value

    hydrated["litellm_params"] = hydrated_params
    return hydrated


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
        model_list = [_hydrate_model_dict(m.to_dict()) for m in models.values()]
    else:
        # Hydrate provided model defs
        model_list = [_hydrate_model_dict(m) for m in model_defs]

    # Get database URL from environment or use default
    # Format: postgresql://user:password@host:port/database
    db_url = os.environ.get(
        "LITELLM_DATABASE_URL",
        "postgresql://postgres:${RUN_CLAUDE_TIMESCALEDB_PASSWORD}@localhost:5433/postgres?sslmode=disable"
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
    # Use the actual master key value directly in config as fallback
    master_key = get_master_key()
    config = {
        "litellm_settings": {
            "drop_params": True,
            "forward_client_headers_to_llm_api": False,
        },
        "general_settings": {
            "master_key": master_key,
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
        print("[ERROR] httpx required for health check", file=sys.stderr)
        return False

    url = get_proxy_url()
    master_key = get_master_key()
    retry_count = 0

    while True:
        try:
            print(f"[HEALTH_CHECK] GET {url}/health with key={master_key}", file=sys.stderr)
            resp = httpx.get(
                f"{url}/health",
                headers={"Authorization": f"Bearer {master_key}"},
                timeout=timeout
            )
            print(f"[HEALTH_CHECK] Response: {resp.status_code} | key={master_key}", file=sys.stderr)

            if resp.status_code == 200:
                print(f"[HEALTH_CHECK] Healthy", file=sys.stderr)
                return True

            # Not healthy yet
            if not wait_for_recovery:
                print(f"[HEALTH_CHECK] Unhealthy (HTTP {resp.status_code})", file=sys.stderr)
                return False

            # Wait and retry if recovery mode enabled
            if max_retries > 0 and retry_count >= max_retries:
                print(f"[HEALTH_CHECK] Max retries reached", file=sys.stderr)
                return False

            retry_count += 1
            print(f"[HEALTH_CHECK] Retry {retry_count}, waiting {HEALTH_CHECK_INTERVAL}s", file=sys.stderr)
            time.sleep(HEALTH_CHECK_INTERVAL)

        except Exception as e:
            print(f"[HEALTH_CHECK_ERROR] {type(e).__name__}: {e}", file=sys.stderr)

            if not wait_for_recovery:
                return False

            # Wait and retry if recovery mode enabled
            if max_retries > 0 and retry_count >= max_retries:
                print(f"[HEALTH_CHECK] Max retries reached", file=sys.stderr)
                return False

            retry_count += 1
            print(f"[HEALTH_CHECK] Retry {retry_count}, waiting {HEALTH_CHECK_INTERVAL}s", file=sys.stderr)
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
    litellm_cmd = get_litellm_command()
    cmd = [litellm_cmd, "--host", DEFAULT_PROXY_HOST, "--port", str(DEFAULT_PROXY_PORT)]
    cmd.extend(["--config", config_path])

    # Start proxy in background
    try:
        # Clone parent environment with additional flags for proxy
        env = os.environ.copy()
        env["STORE_MODEL_IN_DB"] = "True"
        env['USE_PRISMA_MIGRATE'] = "True"
        # Set master key if not already set
        if "LITELLM_MASTER_KEY" not in env:
            env["LITELLM_MASTER_KEY"] = get_master_key()

        print(f"LiteLLM proxy logs saved to: {log_file}", file=sys.stderr)
        print(f"Master key configured: {env.get('LITELLM_MASTER_KEY', 'NOT SET')}", file=sys.stderr)
        print(f"To run litellm locally for debugging, run:", file=sys.stderr)
        print(f" LITELLM_MASTER_KEY={env.get('LITELLM_MASTER_KEY', 'NOT SET')} STORE_MODEL_IN_DB=True USE_PRISMA_MIGRATE=True {' '.join(cmd)}", file=sys.stderr)
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
    master_key = get_master_key()

    try:
        resp = httpx.get(
            f"{url}/model/info",
            headers={"Authorization": f"Bearer {master_key}"},
            timeout=10.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            models = data.get("data", [])
            print(f"[LIST_MODELS] Retrieved {len(models)} model(s) (HTTP {resp.status_code})", file=sys.stderr)
            return models

        # Log API error for non-200 responses
        print(f"[LIST_MODELS_ERROR] Failed to retrieve models (HTTP {resp.status_code})", file=sys.stderr)
        print(f"[API_RESPONSE] {resp.text}", file=sys.stderr)
    except Exception as e:
        print(f"[LIST_MODELS_ERROR] Exception: {type(e).__name__}: {e}", file=sys.stderr)

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
        debug: If True, print detailed debug info on all attempts

    Returns:
        True if model added successfully
    """
    if httpx is None:
        print("[ERROR] httpx not available for model creation", file=sys.stderr)
        return False

    url = get_proxy_url()
    master_key = get_master_key()
    model_name = model_def.get("model_name", "unknown")

    # Hydrate the model definition before logging
    hydrated_model_def = _hydrate_model_dict(model_def)

    print(f"[ATTEMPT] Creating model '{model_name}'", file=sys.stderr)
    print(f"[MASTER_KEY] Using master key: {master_key}", file=sys.stderr)

    try:
        # Always log YAML representation of hydrated model
        if yaml is not None:
            print(f"[MODEL_DEF_YAML]", file=sys.stderr)
            print(yaml.dump(hydrated_model_def, default_flow_style=False), file=sys.stderr)

        if debug:
            request_payload = {
                "method": "POST",
                "url": f"{url}/model/new",
                "headers": {
                    "Authorization": f"Bearer {master_key}",
                    "Content-Type": "application/json",
                },
                "body": hydrated_model_def,
            }
            print(f"[REQUEST_PAYLOAD]", file=sys.stderr)
            if yaml is not None:
                print(yaml.dump(request_payload, default_flow_style=False, sort_keys=False), file=sys.stderr)
            else:
                print(json.dumps(request_payload, indent=2), file=sys.stderr)

        resp = httpx.post(
            f"{url}/model/new",
            headers={
                "Authorization": f"Bearer {master_key}",
                "Content-Type": "application/json",
            },
            json=hydrated_model_def,
            timeout=10.0,
        )

        if resp.status_code in (200, 201):
            print(f"[SUCCESS] Model '{model_name}' created (HTTP {resp.status_code})", file=sys.stderr)
            if debug:
                response_payload = {
                    "status_code": resp.status_code,
                    "headers": dict(resp.headers),
                    "body": None,
                }
                try:
                    response_payload["body"] = resp.json()
                except:
                    response_payload["body"] = resp.text

                print(f"[RESPONSE_PAYLOAD]", file=sys.stderr)
                if yaml is not None:
                    print(yaml.dump(response_payload, default_flow_style=False, sort_keys=False), file=sys.stderr)
                else:
                    print(json.dumps(response_payload, indent=2), file=sys.stderr)
            return True

        # Failure case - always log response
        print(f"[FAILED] Model '{model_name}' creation failed (HTTP {resp.status_code})", file=sys.stderr)
        print(f"[API_RESPONSE] {resp.text}", file=sys.stderr)
        if debug:
            response_payload = {
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "body": None,
            }
            try:
                response_payload["body"] = resp.json()
            except:
                response_payload["body"] = resp.text

            print(f"[RESPONSE_PAYLOAD]", file=sys.stderr)
            if yaml is not None:
                print(yaml.dump(response_payload, default_flow_style=False, sort_keys=False), file=sys.stderr)
            else:
                print(json.dumps(response_payload, indent=2), file=sys.stderr)
        return False

    except Exception as e:
        print(f"[ERROR] Model '{model_name}' creation error: {type(e).__name__}: {e}", file=sys.stderr)
        if debug:
            import traceback
            traceback.print_exc(file=sys.stderr)
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
        print(f"[ERROR] httpx not available for deleting model '{model_id}'", file=sys.stderr)
        return False

    url = get_proxy_url()
    master_key = get_master_key()

    print(f"[ATTEMPT] Deleting model '{model_id}'", file=sys.stderr)

    try:
        resp = httpx.post(
            f"{url}/model/delete",
            headers={
                "Authorization": f"Bearer {master_key}",
                "Content-Type": "application/json",
            },
            json={"id": model_id},
            timeout=10.0,
        )

        if resp.status_code in (200, 204):
            print(f"[SUCCESS] Model '{model_id}' deleted (HTTP {resp.status_code})", file=sys.stderr)
            return True

        # Failure case
        print(f"[FAILED] Model '{model_id}' deletion failed (HTTP {resp.status_code})", file=sys.stderr)
        print(f"[API_RESPONSE] {resp.text}", file=sys.stderr)
        return False

    except Exception as e:
        print(f"[ERROR] Model '{model_id}' deletion error: {type(e).__name__}: {e}", file=sys.stderr)
        return False


def ensure_models(model_defs: list[dict[str, Any]], debug: bool = False, wait_for_recovery: bool = False) -> tuple[int, int]:
    """
    Ensure models are registered with proxy.

    Args:
        model_defs: List of model definitions
        debug: If True, print debug info for each model
        wait_for_recovery: If True, wait for proxy to recover before returning

    Returns:
        Tuple of (added_count, skipped_count)
    """
    print(f"[ENSURE_MODELS] Processing {len(model_defs)} model(s)", file=sys.stderr)

    # Log all model definitions in YAML format
    if model_defs and yaml is not None:
        print(f"[MODELS_YAML_LIST]", file=sys.stderr)
        for i, model_def in enumerate(model_defs):
            print(f"--- Model {i + 1} ---", file=sys.stderr)
            print(yaml.dump(model_def, default_flow_style=False), file=sys.stderr)

    # If wait_for_recovery enabled, wait for proxy to become healthy
    if wait_for_recovery:
        health_check(wait_for_recovery=True, max_retries=HEALTH_CHECK_RETRIES)

    existing = get_model_ids()
    if existing:
        print(f"[INFO] {len(existing)} model(s) already registered", file=sys.stderr)

    added = 0
    skipped = 0
    failed = 0

    for model_def in model_defs:
        model_name = model_def.get("model_name", "")
        if model_name in existing:
            print(f"[SKIP] Model '{model_name}' already registered", file=sys.stderr)
            skipped += 1
            continue

        if add_model(model_def, debug=debug):
            added += 1
        else:
            failed += 1

    # Always show summary
    print(f"[SUMMARY] Added: {added}, Skipped: {skipped}, Failed: {failed}", file=sys.stderr)

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
