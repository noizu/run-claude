"""
LiteLLM proxy lifecycle management.

Handles starting, stopping, health checks, and model management via API.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
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


def _setup_httpx_logging() -> None:
    """Configure httpx and httpcore loggers to write to /var/log/litellm-httpx.log."""
    import logging

    log_path = Path("/var/log/litellm-httpx.log")
    try:
        handler = logging.FileHandler(log_path)
    except (PermissionError, OSError):
        # Fall back to state dir if /var/log is not writable
        fallback = get_state_dir() / "litellm-httpx.log"
        fallback.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(fallback)

    formatter = logging.Formatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)

    logging.getLogger("httpx").setLevel(logging.DEBUG)
    logging.getLogger("httpx").addHandler(handler)
    logging.getLogger("httpcore").setLevel(logging.DEBUG)  # lower-level transport
    logging.getLogger("httpcore").addHandler(handler)


_setup_httpx_logging()


DEFAULT_PROXY_HOST = "127.0.0.1"
DEFAULT_PROXY_PORT = 4444
DEFAULT_PROXY_URL = f"http://{DEFAULT_PROXY_HOST}:{DEFAULT_PROXY_PORT}"
DEFAULT_MASTER_KEY = "sk-litellm-master-key-12345"
DEFAULT_LITELLM_COMMAND = "litellm"

HEALTH_CHECK_TIMEOUT = 60.0
HEALTH_CHECK_RETRIES = 30
HEALTH_CHECK_INTERVAL = 10.0

LITELLM_CONTAINER_NAME = "run-claude-litellm"
COMPOSE_PROJECT = "run-claude-infra"


def _compose_cmd(services_dir: Path, env_file: Path | None = None) -> list[str]:
    """Build base docker compose command with project and file flags."""
    cmd = [
        "docker", "compose",
        "-f", str(services_dir / "docker-compose.yaml"),
        "-f", str(services_dir / "docker-compose.override.yaml"),
        "-p", COMPOSE_PROJECT,
    ]
    if env_file and env_file.exists():
        cmd.extend(["--env-file", str(env_file)])
    return cmd


def get_proxy_url() -> str:
    """Get proxy URL from environment or default."""
    return os.environ.get("LITELLM_PROXY_URL", DEFAULT_PROXY_URL)


def get_master_key() -> str:
    """Get proxy master key from environment or default."""
    return os.environ.get("LITELLM_MASTER_KEY", DEFAULT_MASTER_KEY)


def get_api_key() -> str:
    """Get API key for proxy authentication."""
    return get_master_key()


def get_database_url(debug: bool = False) -> str:
    """Get fully-expanded database URL.

    Reads from LITELLM_DATABASE_URL (set by .env via load_env_file).
    Falls back to constructing from RUN_CLAUDE_TIMESCALEDB_PASSWORD if
    the .env hasn't been exported yet.
    """
    db_url = os.environ.get("LITELLM_DATABASE_URL")
    if db_url:
        return db_url

    # Fallback: construct from individual vars (pre-export state)
    password = os.environ.get("RUN_CLAUDE_TIMESCALEDB_PASSWORD", "")
    if password:
        from .config import construct_database_url
        db_url = construct_database_url(password)
        if debug:
            print(f"DEBUG: Constructed DATABASE_URL from env vars", file=sys.stderr)
        return db_url

    # Last resort: return template (will fail at connection time)
    return "postgresql://postgres:@localhost:5433/postgres?sslmode=disable"


def get_litellm_command() -> str:
    """Get litellm command from environment or default.

    On NixOS systems, use LITELLM_COMMAND=litellm-proxy to specify the uv alias.
    """
    return os.environ.get("LITELLM_COMMAND", DEFAULT_LITELLM_COMMAND)


def get_pid_file() -> Path:
    """Deprecated: proxy now runs in container. PID files no longer used."""
    return get_state_dir() / "proxy.pid"


def get_log_file() -> Path:
    """Deprecated: use get_proxy_logs() for container logs.

    Uses LITELLM_LOG_FILE env var if set, otherwise defaults to /var/log/litellm-proxy.log.
    Falls back to state directory if /var/log is not writable.
    """
    log_path = os.environ.get("LITELLM_LOG_FILE")
    if log_path:
        return Path(log_path)

    # Default to /var/log/litellm-proxy.log
    default_path = Path("/var/log/litellm-proxy.log")

    # Check if /var/log exists and is writable
    if default_path.parent.exists():
        try:
            # Test if we can write to this directory
            default_path.parent.mkdir(parents=True, exist_ok=True)
            return default_path
        except PermissionError:
            pass

    # Fall back to state directory if /var/log is not accessible
    return get_state_dir() / "proxy.log"


def get_config_file() -> Path:
    """Get generated LiteLLM config file path.

    Config is stored in the config dir so docker-compose can mount it.
    """
    return _get_config_dir() / "litellm_config.yaml"


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
class DbStatus:
    """Database container status information."""
    installed: bool = False      # Compose files present in state dir
    container_exists: bool = False  # Container has been created
    running: bool = False        # Container is running
    healthy: bool = False        # Health check passing
    container_id: str | None = None


@dataclass
class ProxyStatus:
    """Proxy status information."""
    running: bool
    pid: int | None = None  # Deprecated: kept for backward compat
    container_id: str | None = None
    healthy: bool = False
    url: str = DEFAULT_PROXY_URL
    model_count: int = 0
    db_healthy: bool = False
    db_status: DbStatus | None = None


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

    # Build model list
    if model_defs is None:
        # Load all available models
        models = load_model_definitions()
        model_list = [_hydrate_model_dict(m.to_dict()) for m in models.values()]
    else:
        # Hydrate provided model defs
        model_list = [_hydrate_model_dict(m) for m in model_defs]

    # Get database URL (loaded from .env at CLI startup)
    debug = "--debug" in sys.argv or "-d" in sys.argv
    db_url = get_database_url(debug=debug)

    print(f"Database connection string: {db_url}", file=sys.stderr)

    # Build config with required LiteLLM settings
    # Use the actual master key value directly in config as fallback
    master_key = get_master_key()

    # Check if callbacks should be enabled (default: enabled)
    enable_callbacks = False # os.environ.get("LITELLM_ENABLE_CALLBACKS", "true").lower() in ("true", "1", "yes")

    litellm_settings = {
        "drop_params": True,
#        "forward_client_headers_to_llm_api": True,
#        "exclude_headers": "[\"authorization\"]",
        "json_logs": False,
        "log_raw_request_response": True,
    }

    # Add provider compatibility callbacks for strict providers (Groq, Cerebras, etc.)
    if enable_callbacks:
        litellm_settings["callbacks"] = [
            "run_claude.callbacks.ProviderCompatCallback",
        ]

    # NOTE: database_url is intentionally NOT included in the config file.
    # In container mode, DATABASE_URL is set via docker-compose environment
    # (pointing to timescaledb:5432 on the internal network).
    # In local mode, it's read from the DATABASE_URL env var loaded from .env.
    # Embedding localhost:5433 here would break the container (which needs
    # the internal docker network hostname).
    config = {
        "litellm_settings": litellm_settings,
        "general_settings": {
            "master_key": master_key,
        },
        "model_list": model_list,
    }

    # Write config file
    config_path = get_config_file()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.dump(config, default_flow_style=False), encoding="utf-8")
    print(config_path)
    return config_path


def get_health_info(timeout: float = HEALTH_CHECK_TIMEOUT) -> dict[str, Any] | None:
    """
    Get full health information from proxy.

    Args:
        timeout: Timeout for health check request

    Returns:
        Health info dict if successful, None on failure
    """
    if httpx is None:
        return None

    url = get_proxy_url()
    master_key = get_master_key()

    try:
        resp = httpx.get(
            f"{url}/health",
            headers={"Authorization": f"Bearer {master_key}"},
            timeout=timeout
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


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
            # print(resp.content)
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
    """Check if LiteLLM proxy container is running."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", LITELLM_CONTAINER_NAME],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and result.stdout.strip().lower() == "true"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_proxy_container_id() -> str | None:
    """Get LiteLLM proxy container ID if it exists."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.Id}}", LITELLM_CONTAINER_NAME],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:12]
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def get_proxy_pid() -> int | None:
    """Deprecated: proxy now runs in a container. Returns None."""
    return None


def start_proxy(config_path: str | None = None, wait: bool = True, empty_config: bool = False, no_db: bool = False, debug: bool = False) -> bool:
    """
    Start LiteLLM proxy via docker compose.

    Args:
        config_path: Deprecated. Config is generated to a fixed location.
        wait: Wait for proxy to become healthy
        empty_config: If True, generate config with empty model list.
                     Models are loaded on-demand via ensure_models().
        no_db: If True, skip automatic database container management.
        debug: Print debug information.

    Returns:
        True if proxy started successfully
    """
    if is_proxy_running() and health_check():
        return True

    # Check Docker availability
    if not is_docker_available():
        print("Error: Docker not found. Please install Docker.", file=sys.stderr)
        return False
    if not is_docker_running():
        print("Error: Docker daemon not running. Please start Docker.", file=sys.stderr)
        return False

    # Ensure infrastructure is installed
    if not is_infrastructure_installed():
        if debug:
            print("Installing infrastructure...", file=sys.stderr)
        install_infrastructure(debug=debug)

    # Ensure database is running (unless explicitly skipped)
    if not no_db and not is_db_container_running():
        print("Starting database container...", file=sys.stderr)
        if not start_db_container(wait=True, debug=debug):
            print("Error: Failed to start database container", file=sys.stderr)
            return False

    # Generate litellm_config.yaml to config dir (skip if already present)
    config_file = get_config_file()
    if not config_file.exists() or empty_config:
        model_defs = [] if empty_config else None
        generate_litellm_config(model_defs=model_defs)

    services_dir = get_services_dir()
    config_dir = _get_config_dir()
    env_file = config_dir / ".env"

    # Build compose command
    cmd = _compose_cmd(services_dir, env_file)

    # Build image if needed
    print("Building LiteLLM image...", file=sys.stderr)
    try:
        result = subprocess.run(
            cmd + ["build", "--quiet", "litellm"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            print(f"Build warning: {result.stderr}", file=sys.stderr)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Error building image: {e}", file=sys.stderr)
        return False

    # Start litellm service (DB is managed explicitly above or skipped via --no-db)
    print("Starting LiteLLM container...", file=sys.stderr)
    try:
        result = subprocess.run(
            cmd + ["up", "-d", "litellm"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"Error starting services:", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return False
        if debug and result.stdout:
            print(result.stdout, file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("Error: Timed out starting services", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: docker compose not found", file=sys.stderr)
        return False

    print(f"LiteLLM proxy starting via docker compose...", file=sys.stderr)
    print(f"  View logs: docker logs -f {LITELLM_CONTAINER_NAME}", file=sys.stderr)

    if wait:
        # Wait for proxy to become healthy
        for _ in range(HEALTH_CHECK_RETRIES):
            if health_check():
                return True
            time.sleep(HEALTH_CHECK_INTERVAL)
        return False

    return True


def stop_proxy() -> bool:
    """
    Stop the LiteLLM proxy container.

    Returns:
        True if proxy was stopped successfully
        False if container couldn't be stopped
    """
    if not is_proxy_running():
        return True

    services_dir = get_services_dir()
    compose_file = services_dir / "docker-compose.yaml"

    if not compose_file.exists():
        # No compose file, try direct container stop
        try:
            subprocess.run(
                ["docker", "stop", LITELLM_CONTAINER_NAME],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    env_file = _get_config_dir() / ".env"
    cmd = _compose_cmd(services_dir, env_file)

    try:
        result = subprocess.run(
            cmd + ["stop", "litellm"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"Error stopping proxy container:", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        print("Error: Timed out stopping proxy container", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: docker compose not found", file=sys.stderr)
        return False


def get_proxy_logs(lines: int = 100) -> str:
    """Get recent logs from the LiteLLM proxy container."""
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(lines), LITELLM_CONTAINER_NAME],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout + result.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def get_status() -> ProxyStatus:
    """Get proxy status."""
    running = is_proxy_running()
    container_id = get_proxy_container_id() if running else None
    healthy = health_check() if running else False

    model_count = 0
    if healthy:
        models = list_models()
        model_count = len(models)

    db_healthy = test_db_connection(debug=True)
    db_status = get_db_status()

    return ProxyStatus(
        running=running,
        container_id=container_id,
        healthy=healthy,
        url=get_proxy_url(),
        model_count=model_count,
        db_healthy=db_healthy,
        db_status=db_status,
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
            model_names = [m.get("model_name", "?") for m in models]
            print(f"[LIST_MODELS] {len(models)} model(s): {', '.join(model_names)}", file=sys.stderr)
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
                    "url": url,
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


def wipe_all_models(debug: bool = False) -> tuple[int, int]:
    """
    Delete all models from the LiteLLM proxy database.

    Args:
        debug: If True, print debug info for each deletion

    Returns:
        Tuple of (deleted_count, failed_count)
    """
    models = list_models()
    if not models:
        print("[WIPE] No models found in database", file=sys.stderr)
        return (0, 0)

    print(f"[WIPE] Found {len(models)} model(s) to delete", file=sys.stderr)

    deleted = 0
    failed = 0

    for model in models:
        # Get model ID - try model_info.id first, then model_name
        model_id = model.get("model_info", {}).get("id")
        if not model_id:
            model_id = model.get("model_name")

        if not model_id:
            print(f"[WIPE] Skipping model with no ID: {model}", file=sys.stderr)
            failed += 1
            continue

        if delete_model(model_id):
            deleted += 1
            if debug:
                print(f"[WIPE] Deleted model: {model_id}", file=sys.stderr)
        else:
            failed += 1
            if debug:
                print(f"[WIPE] Failed to delete model: {model_id}", file=sys.stderr)

    print(f"[WIPE] Completed: {deleted} deleted, {failed} failed", file=sys.stderr)
    return (deleted, failed)


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
    list_models()
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
    # Get database URL (loaded from .env at CLI startup)
    db_url = get_database_url(debug=debug)

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


# =============================================================================
# Infrastructure Management
# =============================================================================

CONTAINER_NAME = "run-claude-timescaledb"


def get_services_dir() -> Path:
    """Get the infrastructure services directory (docker-compose, Dockerfile)."""
    return _get_config_dir() / "services"


def get_dep_dir() -> Path:
    """Deprecated: use get_services_dir(). Kept for backward compatibility."""
    return get_services_dir()


def get_builtin_dep_dir() -> Path:
    """Get the built-in dep directory from package."""
    return Path(__file__).parent / "dep"


def is_docker_available() -> bool:
    """Check if docker command is available."""
    try:
        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def is_docker_running() -> bool:
    """Check if docker daemon is running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_infrastructure(force: bool = False, debug: bool = False) -> bool:
    """
    Install docker-compose files and Dockerfile to services directory.

    Target: ~/.config/run-claude/services/
    Source: built-in dep/ directory from package.

    Args:
        force: Overwrite existing files
        debug: Print debug information

    Returns:
        True if installation successful
    """
    import shutil

    services_dir = get_services_dir()
    builtin_dep = get_builtin_dep_dir()

    # Auto-migrate from old location (~/.local/state/run-claude/dep/)
    old_dep = get_state_dir() / "dep"
    if old_dep.exists() and not services_dir.exists():
        try:
            shutil.move(str(old_dep), str(services_dir))
            print(f"Migrated infrastructure: {old_dep} -> {services_dir}", file=sys.stderr)
        except (OSError, shutil.Error) as e:
            if debug:
                print(f"Warning: Could not migrate old dep dir: {e}", file=sys.stderr)

    # Check if already installed
    compose_file = services_dir / "docker-compose.yaml"
    if compose_file.exists() and not force:
        if debug:
            print(f"Infrastructure already installed at {services_dir}", file=sys.stderr)
        return True

    # Check if built-in dep directory exists
    if not builtin_dep.exists():
        print(f"Error: Built-in dep directory not found: {builtin_dep}", file=sys.stderr)
        return False

    # Create services directory
    services_dir.mkdir(parents=True, exist_ok=True)

    # Files to copy from built-in dep/
    files_to_copy = [
        "docker-compose.yaml",
        "docker-compose.override.yaml",
        "litellm.Dockerfile",
        ".envrc",
    ]

    try:
        for filename in files_to_copy:
            src = builtin_dep / filename
            if src.exists():
                shutil.copy2(src, services_dir / filename)
                if debug:
                    print(f"Installed: {services_dir / filename}", file=sys.stderr)

        # Copy config directory if it exists
        src_config = builtin_dep / "config"
        if src_config.exists():
            dst_config = services_dir / "config"
            if dst_config.exists() and force:
                shutil.rmtree(dst_config)
            if not dst_config.exists():
                shutil.copytree(src_config, dst_config)
                if debug:
                    print(f"Installed: {dst_config}", file=sys.stderr)

        return True

    except (OSError, shutil.Error) as e:
        print(f"Error installing infrastructure: {e}", file=sys.stderr)
        return False


def is_infrastructure_installed() -> bool:
    """Check if infrastructure is installed in services directory."""
    compose_file = get_services_dir() / "docker-compose.yaml"
    return compose_file.exists()


def get_db_container_id() -> str | None:
    """Get the container ID if it exists."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.Id}}", CONTAINER_NAME],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:12]  # Short ID
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def is_db_container_running() -> bool:
    """Check if TimescaleDB container is running."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER_NAME],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and result.stdout.strip().lower() == "true"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def is_db_container_healthy() -> bool:
    """Check if TimescaleDB container is healthy."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Health.Status}}", CONTAINER_NAME],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and result.stdout.strip().lower() == "healthy"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def wait_for_db_healthy(timeout: float = 60.0, interval: float = 2.0, debug: bool = False) -> bool:
    """
    Wait for database container to become healthy.

    Args:
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        debug: Print debug information

    Returns:
        True if container became healthy within timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        if is_db_container_healthy():
            if debug:
                print("Database container is healthy", file=sys.stderr)
            return True

        if not is_db_container_running():
            if debug:
                print("Database container stopped unexpectedly", file=sys.stderr)
            return False

        if debug:
            elapsed = int(time.time() - start)
            print(f"Waiting for database to become healthy... ({elapsed}s)", file=sys.stderr)

        time.sleep(interval)

    if debug:
        print(f"Database failed to become healthy within {timeout}s", file=sys.stderr)
    return False


def _get_config_dir() -> Path:
    """Get the config directory for .env file."""
    run_claude_home = os.environ.get("RUN_CLAUDE_HOME")
    if run_claude_home:
        return Path(run_claude_home)

    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "run-claude"

    return Path.home() / ".config" / "run-claude"


def start_db_container(wait: bool = True, debug: bool = False) -> bool:
    """
    Start the TimescaleDB container.

    Args:
        wait: Wait for container to become healthy
        debug: Print debug information

    Returns:
        True if container started successfully
    """
    # Check docker availability
    if not is_docker_available():
        print("Error: Docker not found. Please install Docker.", file=sys.stderr)
        return False

    if not is_docker_running():
        print("Error: Docker daemon not running. Please start Docker.", file=sys.stderr)
        return False

    # Ensure infrastructure is installed
    if not is_infrastructure_installed():
        if debug:
            print("Installing infrastructure...", file=sys.stderr)
        if not install_infrastructure(debug=debug):
            return False

    # Check if already running
    if is_db_container_running():
        if debug:
            print("Database container already running", file=sys.stderr)
        return True

    services_dir = get_services_dir()
    env_file = _get_config_dir() / ".env"

    if not env_file.exists():
        print(f"Warning: .env file not found at {env_file}", file=sys.stderr)
        print("Run 'run-claude secrets export' to create it", file=sys.stderr)

    # Build compose command
    cmd = _compose_cmd(services_dir, env_file)
    cmd.extend(["up", "-d", "timescaledb"])

    if debug:
        print(f"Running: {' '.join(cmd)}", file=sys.stderr)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            print(f"Error starting database container:", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return False

        if debug and result.stdout:
            print(result.stdout, file=sys.stderr)

        # Wait for container to become healthy
        if wait:
            if debug:
                print("Waiting for database to become healthy...", file=sys.stderr)
            return wait_for_db_healthy(timeout=60.0, debug=debug)

        return True

    except subprocess.TimeoutExpired:
        print("Error: Timed out starting database container", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: docker compose not found", file=sys.stderr)
        return False


def stop_db_container(remove: bool = False, debug: bool = False) -> bool:
    """
    Stop the TimescaleDB container.

    Args:
        remove: If True, also remove container and volumes
        debug: Print debug information

    Returns:
        True if container stopped successfully
    """
    if not is_docker_available():
        if debug:
            print("Docker not available", file=sys.stderr)
        return True  # Nothing to stop

    services_dir = get_services_dir()
    compose_file = services_dir / "docker-compose.yaml"

    if not compose_file.exists():
        if debug:
            print("No compose file found, nothing to stop", file=sys.stderr)
        return True

    env_file = _get_config_dir() / ".env"
    cmd = _compose_cmd(services_dir, env_file)

    if remove:
        cmd.extend(["down", "-v"])  # Remove volumes too
    else:
        cmd.append("stop")

    if debug:
        print(f"Running: {' '.join(cmd)}", file=sys.stderr)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            print(f"Error stopping database container:", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return False

        if debug and result.stdout:
            print(result.stdout, file=sys.stderr)

        return True

    except subprocess.TimeoutExpired:
        print("Error: Timed out stopping database container", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: docker compose not found", file=sys.stderr)
        return False


def get_db_status() -> DbStatus:
    """Get database container status."""
    status = DbStatus()

    # Check if infrastructure is installed
    status.installed = is_infrastructure_installed()

    # Check container status
    container_id = get_db_container_id()
    status.container_exists = container_id is not None
    status.container_id = container_id

    if status.container_exists:
        status.running = is_db_container_running()
        if status.running:
            status.healthy = is_db_container_healthy()

    return status


DEFAULT_PRISMA_COMMAND = "prisma"


def get_prisma_command() -> str:
    """Get prisma command from environment or default.

    On NixOS systems, use PRISMA_COMMAND to specify the command (e.g., 'uv run prisma').
    """
    return os.environ.get("PRISMA_COMMAND", DEFAULT_PRISMA_COMMAND)


def run_prisma_migrate(debug: bool = False) -> bool:
    """
    Run prisma migrate using the same config as LiteLLM proxy.

    This sets up the environment variables and database URL the same way
    as start_proxy() does, then runs prisma db push.

    Args:
        debug: Print debug information

    Returns:
        True if migration succeeded
    """
    import shlex

    # Get database URL (loaded from .env at CLI startup)
    db_url = get_database_url(debug=debug)

    print(f"Database URL: {db_url}", file=sys.stderr)

    # Find litellm's prisma schema
    try:
        import litellm
        litellm_path = Path(litellm.__file__).parent
        schema_path = litellm_path / "proxy" / "schema.prisma"

        if not schema_path.exists():
            # Try alternate locations
            alt_paths = [
                litellm_path / "proxy" / "prisma" / "schema.prisma",
                litellm_path / "schema.prisma",
            ]
            for alt in alt_paths:
                if alt.exists():
                    schema_path = alt
                    break

        if not schema_path.exists():
            print(f"Error: Could not find prisma schema file", file=sys.stderr)
            print(f"Searched in: {litellm_path}", file=sys.stderr)
            return False

        if debug:
            print(f"Using schema: {schema_path}", file=sys.stderr)

    except ImportError:
        print("Error: litellm not installed", file=sys.stderr)
        return False

    # Build environment for prisma
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url
    env["STORE_MODEL_IN_DB"] = "True"
    env["USE_PRISMA_MIGRATE"] = "True"

    # Get prisma command - supports custom command via PRISMA_COMMAND env var
    prisma_cmd = get_prisma_command()
    # Split command in case it's "uv run prisma" or similar
    cmd = shlex.split(prisma_cmd) + ["db", "push", f"--schema={schema_path}"]

    if debug:
        print(f"Running: {' '.join(cmd)}", file=sys.stderr)

    try:
        result = subprocess.run(
            cmd,
            env=env,
            timeout=120,
        )

        if result.returncode != 0:
            print(f"Prisma migrate failed with exit code {result.returncode}", file=sys.stderr)
            return False

        return True

    except FileNotFoundError:
        print("Error: prisma command not found", file=sys.stderr)
        print("", file=sys.stderr)
        print("Install with: pip install prisma", file=sys.stderr)
        print("", file=sys.stderr)
        # Check if using uv for litellm
        litellm_cmd = get_litellm_command()
        if "uv" in litellm_cmd:
            print("Note: You appear to be using uv. Try:", file=sys.stderr)
            print("  PRISMA_COMMAND='uv run prisma' run-claude db migrate", file=sys.stderr)
            print("", file=sys.stderr)
            print("Or add to your shell config:", file=sys.stderr)
            print("  export PRISMA_COMMAND='uv run prisma'", file=sys.stderr)
        else:
            print("On NixOS or with uv, you may need to set PRISMA_COMMAND:", file=sys.stderr)
            print("  export PRISMA_COMMAND='uv run prisma'", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print("Error: Prisma migrate timed out", file=sys.stderr)
        return False
