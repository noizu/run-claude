"""
Configuration management for run-claude.

Loads secrets and configuration from ~/.config/run-claude/.secrets
Supports both environment variables and dictionary access patterns.
"""

from __future__ import annotations

import getpass
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
# Quick setup: run `run-claude setup` for an interactive wizard.
# Manual edit: after editing this file, run `run-claude secrets export`
# to generate the .env file used by Docker Compose.

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
# Uncomment and fill in keys for providers you want to use.
# See available profiles with: run-claude profiles list
# Tip: run `run-claude setup` for an interactive wizard.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# OpenAI — https://platform.openai.com/api-keys
# OPENAI_API_KEY: ""

# Google Gemini — https://aistudio.google.com/apikey
# GEMINI_API_KEY: ""

# Cerebras — https://cloud.cerebras.ai/
# CEREBRAS_API_KEY: ""
# CEREBRAS_SUB_KEY: ""

# Z.AI
# ZAI_API_KEY: ""
# ZAI_SUB_KEY: ""

# Groq — https://console.groq.com/keys
# GROQ_API_KEY: ""

# xAI Grok — https://console.x.ai/
# GROK_API_KEY: ""

# DeepSeek — https://platform.deepseek.com/api-keys
# DEEPSEEK_API_KEY: ""

# Mistral — https://console.mistral.ai/api-keys/
# MISTRAL_API_KEY: ""

# Perplexity — https://www.perplexity.ai/settings/api
# PERPLEXITY_API_KEY: ""

# Azure OpenAI — https://portal.azure.com/
# AZURE_OPENAI_API_KEY: ""
# AZURE_OPENAI_ENDPOINT: ""
# AZURE_OPENAI_API_VERSION: "2024-02-15-preview"
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
    print(f"Run `run-claude setup` to configure API keys interactively.", file=sys.stderr)

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


# ---------------------------------------------------------------------------
# Provider registry — shared by setup wizard and secrets template
# ---------------------------------------------------------------------------

PROVIDERS: list[dict[str, Any]] = [
    {"key": "ANTHROPIC_API_KEY", "name": "Anthropic", "url": "https://console.anthropic.com/api_keys", "required": True},
    {"key": "OPENAI_API_KEY", "name": "OpenAI", "url": "https://platform.openai.com/api-keys"},
    {"key": "GEMINI_API_KEY", "name": "Google Gemini", "url": "https://aistudio.google.com/apikey"},
    {"key": "CEREBRAS_API_KEY", "name": "Cerebras", "url": "https://cloud.cerebras.ai/"},
    {"key": "CEREBRAS_SUB_KEY", "name": "Cerebras Pro (subscription)", "url": "https://cloud.cerebras.ai/"},
    {"key": "ZAI_API_KEY", "name": "Z.AI", "url": ""},
    {"key": "ZAI_SUB_KEY", "name": "Z.AI Pro (subscription)", "url": ""},
    {"key": "GROQ_API_KEY", "name": "Groq", "url": "https://console.groq.com/keys"},
    {"key": "GROK_API_KEY", "name": "xAI Grok", "url": "https://console.x.ai/"},
    {"key": "DEEPSEEK_API_KEY", "name": "DeepSeek", "url": "https://platform.deepseek.com/api-keys"},
    {"key": "MISTRAL_API_KEY", "name": "Mistral", "url": "https://console.mistral.ai/api-keys/"},
    {"key": "PERPLEXITY_API_KEY", "name": "Perplexity", "url": "https://www.perplexity.ai/settings/api"},
]

# Placeholder values that indicate unconfigured keys
_PLACEHOLDER_VALUES = {"sk-your-key-here", "", "your-key-here"}


def _is_placeholder(value: str | None) -> bool:
    """Check if a secret value is a placeholder (not actually configured)."""
    return value is None or value.strip() in _PLACEHOLDER_VALUES


# ---------------------------------------------------------------------------
# Phase 1: Fix credential loading chain
# ---------------------------------------------------------------------------

def load_secrets_into_env(debug: bool = False) -> dict[str, str]:
    """Load .secrets YAML directly into os.environ.

    This is the core fix for the broken credential chain: secrets go
    directly into the process environment without requiring the .env
    intermediary.

    Does NOT override existing environment variables.

    Returns dict of loaded key-value pairs.
    """
    secrets_file = get_secrets_file()
    if not secrets_file.exists():
        if debug:
            print(f"DEBUG: .secrets not found, skipping env load", file=sys.stderr)
        return {}

    try:
        cfg = load_secrets(debug=debug)
        env_vars = cfg.to_env()

        loaded = {}
        for key, value in env_vars.items():
            if key not in os.environ:
                os.environ[key] = value
                loaded[key] = value

        # Also derive DATABASE_URL if we have the password
        db_password = env_vars.get("RUN_CLAUDE_TIMESCALEDB_PASSWORD", "")
        if db_password and not _is_placeholder(db_password):
            db_url = construct_database_url(db_password)
            for derived_key in ("LITELLM_DATABASE_URL", "DATABASE_URL"):
                if derived_key not in os.environ:
                    os.environ[derived_key] = db_url
                    loaded[derived_key] = db_url

        if debug:
            print(f"DEBUG: Loaded {len(loaded)} secrets into env", file=sys.stderr)

        return loaded

    except Exception as e:
        if debug:
            print(f"DEBUG: Error loading secrets into env: {e}", file=sys.stderr)
        return {}


def _auto_export_env_if_stale(debug: bool = False) -> bool:
    """Auto-export .env from .secrets if stale or missing.

    Keeps the .env file in sync for Docker Compose without requiring
    manual `run-claude secrets export`.

    Returns True if export happened.
    """
    secrets_file = get_secrets_file()
    env_file = get_env_file()

    if not secrets_file.exists():
        return False

    needs_export = False
    if not env_file.exists():
        needs_export = True
    else:
        try:
            if secrets_file.stat().st_mtime > env_file.stat().st_mtime:
                needs_export = True
        except OSError:
            needs_export = True

    if needs_export:
        try:
            export_env_file(debug=debug)
            if debug:
                print(f"DEBUG: Auto-exported .env (secrets were newer)", file=sys.stderr)
            return True
        except Exception as e:
            if debug:
                print(f"DEBUG: Auto-export failed: {e}", file=sys.stderr)
            return False

    return False


def ensure_secrets_and_env(debug: bool = False) -> None:
    """Unified startup orchestrator for credentials.

    Replaces the fragmented init sequence in main(). Correct order:
    1. Ensure .secrets template exists (so file is there before load)
    2. Load .secrets directly into os.environ
    3. Auto-export .env if stale (for Docker Compose)
    4. Load .env for any additional vars (backward compat)
    """
    # 1. Create .secrets if missing (first run)
    ensure_secrets_template(debug=debug)

    # 2. Load secrets into process environment
    load_secrets_into_env(debug=debug)

    # 3. Keep .env in sync for Docker Compose
    _auto_export_env_if_stale(debug=debug)

    # 4. Pick up any .env-only vars (backward compat)
    load_env_file(debug=debug)


# ---------------------------------------------------------------------------
# Phase 3: Interactive setup wizard
# ---------------------------------------------------------------------------

def _mask_key(value: str) -> str:
    """Mask an API key for display, showing first 8 and last 4 chars."""
    if len(value) > 12:
        return value[:8] + "..." + value[-4:]
    return "****"


def _provider_status(key: str, secrets: dict[str, str]) -> str:
    """Return status string for a provider key."""
    config_val = secrets.get(key)
    env_val = os.environ.get(key)
    has_config = not _is_placeholder(config_val)
    has_env = env_val is not None and not _is_placeholder(env_val)

    if has_config:
        return f"configured ({_mask_key(config_val)})"  # type: ignore[arg-type]
    elif has_env:
        return f"in env ({_mask_key(env_val)})"  # type: ignore[arg-type]
    else:
        return "not set"


def _print_provider_menu(secrets: dict[str, str]) -> None:
    """Print the numbered provider menu with status indicators."""
    print(f"\n  {'#':<4} {'Provider':<28} {'Status'}")
    print(f"  {'─' * 4} {'─' * 28} {'─' * 24}")
    for i, provider in enumerate(PROVIDERS, 1):
        key = provider["key"]
        name = provider["name"]
        required = " *" if provider.get("required") else ""
        status = _provider_status(key, secrets)

        # Color-code status
        if status.startswith("configured"):
            marker = "+"
        elif status.startswith("in env"):
            marker = "~"
        else:
            marker = " "

        print(f"  {i:<4} {marker} {name + required:<26} {status}")

    print(f"\n  * = recommended    + = configured    ~ = found in environment")
    print(f"  Enter number to configure, 'done' to save and exit, 'q' to quit without saving")


def run_setup_wizard(reconfigure: bool = False, debug: bool = False) -> Path:
    """Interactive menu-driven setup wizard for API keys and credentials.

    Shows a numbered list of providers with their current status.
    User picks a number to configure, enters the key, returns to the menu.
    Type 'done' to save, 'q' to quit without saving.

    Args:
        reconfigure: If True, allow editing existing configuration
        debug: Enable debug output

    Returns path to the written .secrets file.
    """
    secrets_file = get_secrets_file()
    current_secrets: dict[str, str] = {}

    # Load existing secrets
    if secrets_file.exists():
        try:
            cfg = load_secrets(debug=debug)
            current_secrets = cfg.to_env()
        except Exception:
            pass

    # Banner
    print(f"\n{'=' * 60}")
    print(f"  run-claude Setup Wizard")
    print(f"{'=' * 60}")

    # Menu loop
    while True:
        _print_provider_menu(current_secrets)

        try:
            choice = input("\n  > ").strip().lower()
        except EOFError:
            choice = "q"

        if choice in ("q", "quit"):
            print("\n  Quit without saving.\n")
            return secrets_file

        if choice in ("done", "d", ""):
            break

        # Parse number
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(PROVIDERS):
                print(f"  Invalid number. Enter 1-{len(PROVIDERS)}.")
                continue
        except ValueError:
            print(f"  Enter a number (1-{len(PROVIDERS)}), 'done', or 'q'.")
            continue

        provider = PROVIDERS[idx]
        key = provider["key"]
        name = provider["name"]
        url = provider.get("url", "")

        print(f"\n  ── {name} ──")
        if url:
            print(f"  Get key from: {url}")

        # Show current sources
        config_val = current_secrets.get(key)
        env_val = os.environ.get(key)
        has_config = not _is_placeholder(config_val)
        has_env = env_val is not None and not _is_placeholder(env_val)

        if has_env and not has_config:
            masked = _mask_key(env_val)  # type: ignore[arg-type]
            try:
                answer = input(f"  Found in environment ({masked}). Use it? [Y/n/enter manually]: ").strip().lower()
            except EOFError:
                answer = ""
            if answer in ("", "y", "yes"):
                current_secrets[key] = env_val  # type: ignore[assignment]
                print(f"  Saved from environment.")
                continue
            elif answer in ("n", "no"):
                # Remove the key if user explicitly declines
                current_secrets.pop(key, None)
                print(f"  Cleared.")
                continue
            # else: fall through to manual entry

        if has_config:
            masked = _mask_key(config_val)  # type: ignore[arg-type]
            print(f"  Currently: {masked}")
            print(f"  Enter new key, press Enter to keep, or 'clear' to remove.")

        value = getpass.getpass(f"  API key: ")

        if value.strip().lower() == "clear":
            current_secrets.pop(key, None)
            print(f"  Cleared {name}.")
        elif value:
            current_secrets[key] = value
            print(f"  Saved {name}.")
        elif has_config:
            print(f"  Kept existing value.")
        else:
            print(f"  Skipped.")

    # Auto-generate infrastructure secrets (preserve existing)
    for infra_key, generator in [
        ("RUN_CLAUDE_TIMESCALEDB_PASSWORD", generate_random_password),
        ("LITELLM_MASTER_KEY", generate_master_key),
    ]:
        if not current_secrets.get(infra_key) or _is_placeholder(current_secrets.get(infra_key)):
            current_secrets[infra_key] = generator()

    # Write .secrets YAML
    _require_yaml()
    secrets_file.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# run-claude Secrets Configuration",
        "# Generated by: run-claude setup",
        f"# Location: {secrets_file}",
        "# Permissions: chmod 600 (owner read/write only)",
        "",
    ]
    for k, v in current_secrets.items():
        lines.append(f'{k}: "{v}"')

    secrets_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        secrets_file.chmod(0o600)
    except OSError:
        pass

    # Export .env and load into current process
    try:
        export_env_file(debug=debug)
    except Exception:
        pass
    load_secrets_into_env(debug=debug)

    # Summary
    configured = [p["name"] for p in PROVIDERS if not _is_placeholder(current_secrets.get(p["key"]))]
    not_set = [p["name"] for p in PROVIDERS if _is_placeholder(current_secrets.get(p["key"]))]

    print(f"\n{'─' * 60}")
    print(f"  Setup complete!")
    print(f"{'─' * 60}")
    if configured:
        print(f"\n  Configured: {', '.join(configured)}")
    if not_set:
        print(f"  Not set:    {', '.join(not_set)}")
    print(f"\n  Secrets:    {secrets_file}")
    print(f"  Env file:   {get_env_file()}")
    print(f"\n  Next steps:")
    print(f"    run-claude proxy start    # Start the LiteLLM proxy")
    print(f"    run-claude status         # Check current state")
    print(f"    run-claude setup          # Reconfigure later\n")

    return secrets_file
