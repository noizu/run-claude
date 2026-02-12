"""
Configuration management for run-claude.

Loads secrets and configuration from ~/.config/run-claude/.secrets
Supports both environment variables and dictionary access patterns.
"""

from __future__ import annotations

import os
import secrets
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


@dataclass
class SecretsConfig:
    """Container for secrets loaded from config file."""
    _data: dict[str, Any]

    def __getitem__(self, key: str) -> str:
        """Get a secret value by key."""
        if key not in self._data:
            raise KeyError(f"Secret key not found: {key}")
        value = self._data[key]
        if value is None:
            raise ValueError(f"Secret key is None: {key}")
        return str(value)

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get a secret value with optional default."""
        if key in self._data:
            value = self._data[key]
            return str(value) if value is not None else default
        return default

    def to_env(self) -> dict[str, str]:
        """Convert secrets to environment variable dict."""
        env = {}
        for key, value in self._data.items():
            if value is not None:
                env[key] = str(value)
        return env


def get_secrets_file() -> Path:
    """Get path to secrets configuration file.

    Priority order:
    1. $RUN_CLAUDE_HOME/.secrets (if set)
    2. $XDG_CONFIG_HOME/run-claude/.secrets (if set)
    3. ~/.config/run-claude/.secrets (default)
    """
    # Check RUN_CLAUDE_HOME first (allows custom installation directory)
    run_claude_home = os.environ.get("RUN_CLAUDE_HOME")
    if run_claude_home:
        return Path(run_claude_home) / ".secrets"

    # Fall back to XDG_CONFIG_HOME
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        base = Path(xdg_config)
    else:
        base = Path.home() / ".config"
    return base / "run-claude" / ".secrets"


def _require_yaml() -> None:
    """Raise error if PyYAML not installed."""
    if yaml is None:
        raise RuntimeError(
            "PyYAML is required for config loading.\n"
            "Install with: pip install pyyaml"
        )


def get_env_file() -> Path:
    """Get path to .env file.

    Priority order:
    1. $RUN_CLAUDE_HOME/.env (if set)
    2. $XDG_CONFIG_HOME/run-claude/.env (if set)
    3. ~/.config/run-claude/.env (default)
    """
    run_claude_home = os.environ.get("RUN_CLAUDE_HOME")
    if run_claude_home:
        return Path(run_claude_home) / ".env"

    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        base = Path(xdg_config)
    else:
        base = Path.home() / ".config"
    return base / "run-claude" / ".env"


def load_env_file(env_path: Path | None = None, debug: bool = False) -> dict[str, str]:
    """Load .env file into os.environ. Does NOT override existing vars.

    Args:
        env_path: Path to .env file. Defaults to ~/.config/run-claude/.env
        debug: Enable debug output

    Returns:
        Dict of loaded key-value pairs.
    """
    if env_path is None:
        env_path = get_env_file()

    if not env_path.exists():
        if debug:
            print(f"DEBUG: .env file not found: {env_path}", file=sys.stderr)
        return {}

    loaded = {}
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Strip surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            loaded[key] = value
            # Don't override existing env vars
            if key not in os.environ:
                os.environ[key] = value

        if debug:
            print(f"DEBUG: Loaded {len(loaded)} vars from {env_path}", file=sys.stderr)

    except Exception as e:
        if debug:
            print(f"DEBUG: Error loading .env file: {e}", file=sys.stderr)

    return loaded


def construct_database_url(
    password: str,
    host: str = "localhost",
    port: int = 5433,
    user: str = "postgres",
    database: str = "postgres",
) -> str:
    """Build fully-expanded DATABASE_URL. Single source of truth."""
    return f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode=disable"


def generate_master_key() -> str:
    """Generate sk-litellm-{32-char-random} format key."""
    return f"sk-litellm-{generate_random_password(32)}"


def validate_env(required: list[str] | None = None) -> list[str]:
    """Check for missing/unexpanded env vars. Returns list of problems."""
    problems = []

    # Check for literal ${...} in values (unexpanded vars)
    for key, value in os.environ.items():
        if key.startswith("RUN_CLAUDE_") or key.startswith("LITELLM_"):
            if "${" in value and "}" in value:
                problems.append(f"{key} contains unexpanded variable reference: {value}")

    # Check required vars are set
    if required:
        for var in required:
            if not os.environ.get(var):
                problems.append(f"{var} is not set")

    return problems


def generate_random_password(length: int = 32) -> str:
    """Generate a cryptographically secure random password.

    Args:
        length: Password length (default 32 characters)

    Returns:
        Random password with mixed case, numbers, and symbols
    """
    # Use secure random generator
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def load_secrets(debug: bool = False) -> SecretsConfig:
    """
    Load secrets from configuration file.

    Looks for ~/.config/run-claude/.secrets (YAML format)
    Returns a SecretsConfig object for accessing secret values.

    Example .secrets file:
    ---
    RUN_CLAUDE_TIMESCALEDB_PASSWORD: "your-password-here"
    ANTHROPIC_API_KEY: "sk-..."
    OTHER_SECRET: "value"
    """
    _require_yaml()

    secrets_file = get_secrets_file()

    if debug:
        print(f"DEBUG: Loading secrets from: {secrets_file}", file=sys.stderr)
        print(f"DEBUG: Secrets file exists: {secrets_file.exists()}", file=sys.stderr)

    if not secrets_file.exists():
        if debug:
            print(f"DEBUG: Secrets file not found, returning empty config", file=sys.stderr)
        return SecretsConfig(_data={})

    try:
        content = secrets_file.read_text(encoding="utf-8")
        data = yaml.safe_load(content) or {}

        if not isinstance(data, dict):
            raise ValueError(f"Secrets file must contain a YAML dictionary, got {type(data)}")

        if debug:
            keys = list(data.keys())
            print(f"DEBUG: Loaded secrets with keys: {keys}", file=sys.stderr)

        return SecretsConfig(_data=data)

    except Exception as e:
        print(f"Error loading secrets from {secrets_file}: {e}", file=sys.stderr)
        raise


def create_secrets_template(generate_passwords: bool = True, expand_vars: bool = False) -> str:
    """Generate a template .secrets file with documentation.

    Args:
        generate_passwords: If True (default), generate random passwords for
            database and master key fields. Set False for placeholder values.
        expand_vars: If True, expand any environment variables in values

    Returns:
        YAML template string with required and optional variables documented
    """
    db_password = generate_random_password() if generate_passwords else "your-postgres-password"
    master_key = generate_master_key() if generate_passwords else "sk-litellm-your-master-key-here"

    template = f"""# run-claude Secrets Configuration
# Location: ~/.config/run-claude/.secrets
# Permissions: chmod 600 (owner read/write only)
#
# WARNING: This file contains sensitive information!
# - Never commit to version control
# - Restrict file permissions to owner only
# - Keep backups in secure location
#
# After editing, run: run-claude secrets export
# This generates the .env file used by Docker Compose and the CLI.

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REQUIRED: Set your API key
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Get from: https://console.anthropic.com/api_keys
ANTHROPIC_API_KEY: "sk-your-key-here"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTO-GENERATED (change if needed)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Database password for TimescaleDB
RUN_CLAUDE_TIMESCALEDB_PASSWORD: "{db_password}"

# LiteLLM proxy master key (used for proxy API authentication)
LITELLM_MASTER_KEY: "{master_key}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OPTIONAL (Uncomment to override defaults)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Database user (default: postgres)
# RUN_CLAUDE_TIMESCALEDB_USER: "postgres"

# Database name (default: postgres)
# RUN_CLAUDE_TIMESCALEDB_DATABASE: "postgres"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OPTIONAL PROVIDER KEYS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# OPENAI_API_KEY: ""
# CEREBRAS_API_KEY: ""
# GROQ_API_KEY: ""
# TOGETHER_API_KEY: ""
"""
    return template


def ensure_secrets_template(force: bool = False, generate_passwords: bool = True, debug: bool = False) -> Path:
    """
    Ensure secrets template exists.

    Creates a template .secrets file if it doesn't exist (and force=False),
    with auto-generated passwords by default.

    Args:
        force: Overwrite existing file
        generate_passwords: Generate random passwords for required fields (default True)
        debug: Enable debug output

    Returns the path to the secrets file.
    """
    secrets_file = get_secrets_file()

    if debug:
        print(f"DEBUG: Checking secrets file: {secrets_file}", file=sys.stderr)

    if secrets_file.exists() and not force:
        if debug:
            print(f"DEBUG: Secrets file already exists", file=sys.stderr)
        return secrets_file

    # Create parent directory
    secrets_file.parent.mkdir(parents=True, exist_ok=True)

    # Write template (passwords auto-generated by default)
    template = create_secrets_template(generate_passwords=generate_passwords)
    secrets_file.write_text(template, encoding="utf-8")

    # Restrict permissions to owner only
    try:
        secrets_file.chmod(0o600)
        if debug:
            print(f"DEBUG: Created secrets file with restricted permissions: {secrets_file}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not set file permissions: {e}", file=sys.stderr)

    print(f"Created secrets template: {secrets_file}", file=sys.stderr)
    print(f"Secure passwords generated automatically.", file=sys.stderr)
    print(f"Please edit {secrets_file} and add your ANTHROPIC_API_KEY", file=sys.stderr)

    return secrets_file


def export_env_file(debug: bool = False) -> Path:
    """
    Export secrets to Docker Compose .env file.

    Converts secrets (YAML) to .env format suitable for `docker compose`.
    Docker Compose will automatically load this file and make variables available.

    Priority order for output location:
    1. $RUN_CLAUDE_HOME/.env (if set)
    2. $XDG_CONFIG_HOME/run-claude/.env (if set)
    3. ~/.config/run-claude/.env (default)

    Args:
        debug: Enable debug output

    Returns the path to the generated .env file.
    """
    env_file = get_env_file()

    if debug:
        print(f"DEBUG: Exporting secrets to env file: {env_file}", file=sys.stderr)

    try:
        secrets = load_secrets(debug=debug)
        env_vars = secrets.to_env()

        # Add derived variables
        db_password = env_vars.get("RUN_CLAUDE_TIMESCALEDB_PASSWORD", "")
        if db_password and db_password != "your-postgres-password":
            db_url = construct_database_url(db_password)
            env_vars["LITELLM_DATABASE_URL"] = db_url
            env_vars["DATABASE_URL"] = db_url
            env_vars["POSTGRES_PASSWORD"] = db_password

        # Write .env file - Docker Compose will load automatically
        lines = [f"{key}={value}" for key, value in env_vars.items()]
        env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # Restrict permissions for .env file too
        try:
            env_file.chmod(0o600)
            if debug:
                print(f"DEBUG: Created .env file with restricted permissions", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not set .env file permissions: {e}", file=sys.stderr)

        if debug:
            print(f"DEBUG: Exported {len(env_vars)} secrets to .env", file=sys.stderr)

        return env_file

    except Exception as e:
        print(f"Error exporting secrets: {e}", file=sys.stderr)
        raise
