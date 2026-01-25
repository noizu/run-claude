#!/usr/bin/env python3
"""
run-claude - Agent shim controller for Claude.

Directory-aware model routing via LiteLLM proxy.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from pathlib import Path


def main() -> int:
    # Ensure config is initialized on first run
    from . import profiles, config
    profiles.ensure_initialized()

    # Ensure secrets template exists
    debug = "--debug" in sys.argv or "-d" in sys.argv
    config.ensure_secrets_template(debug=debug)

    parser = argparse.ArgumentParser(
        prog="run-claude",
        description="Agent shim controller for Claude - launch claude with mode list profile",
    )
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug output")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # enter
    enter_p = subparsers.add_parser("enter", help="Enter a shimmed directory")
    enter_p.add_argument("token", help="Directory token")
    enter_p.add_argument("profile", help="Profile name")
    enter_p.add_argument("--dir", help="Directory path (default: cwd)")

    # leave
    leave_p = subparsers.add_parser("leave", help="Leave a shimmed directory")
    leave_p.add_argument("token", help="Directory token")

    # janitor
    janitor_p = subparsers.add_parser("janitor", help="Clean up expired leases")
    janitor_p.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
    janitor_p.add_argument("--force", "-f", action="store_true", help="Run even if recently ran")

    # set-folder
    setfolder_p = subparsers.add_parser("set-folder", help="Configure current directory")
    setfolder_p.add_argument("profile", help="Profile name")
    setfolder_p.add_argument("--dir", help="Directory path (default: cwd)")

    # status
    subparsers.add_parser("status", help="Show current state")

    # env
    env_p = subparsers.add_parser("env", help="Print environment variables for a profile")
    env_p.add_argument("profile", help="Profile name")
    env_p.add_argument("--export", "-e", action="store_true", help="Print export statements")

    # proxy subcommands
    proxy_p = subparsers.add_parser("proxy", help="Proxy management")
    proxy_sub = proxy_p.add_subparsers(dest="proxy_command")
    proxy_start_p = proxy_sub.add_parser("start", help="Start proxy")
    proxy_start_p.add_argument("--no-db", action="store_true", help="Don't auto-start database container")
    proxy_stop_p = proxy_sub.add_parser("stop", help="Stop proxy")
    proxy_stop_p.add_argument("--with-db", action="store_true", help="Also stop database container")
    proxy_stop_p.add_argument("--all", action="store_true", help="Stop everything and remove containers")
    proxy_sub.add_parser("status", help="Proxy status")
    proxy_sub.add_parser("health", help="Health check")
    proxy_sub.add_parser("db-test", help="Test database connection")

    # db subcommands
    db_p = subparsers.add_parser("db", help="Database container management")
    db_sub = db_p.add_subparsers(dest="db_command")
    db_sub.add_parser("start", help="Start database container")
    db_stop_p = db_sub.add_parser("stop", help="Stop database container")
    db_stop_p.add_argument("--remove", "-r", action="store_true", help="Remove container and volumes")
    db_sub.add_parser("status", help="Database container status")

    # profiles subcommands
    profiles_p = subparsers.add_parser("profiles", help="Profile management")
    profiles_sub = profiles_p.add_subparsers(dest="profiles_command")
    profiles_sub.add_parser("list", help="List available profiles")
    show_p = profiles_sub.add_parser("show", help="Show profile details")
    show_p.add_argument("name", help="Profile name")
    profiles_sub.add_parser("install", help="Install built-in profiles to user config")

    # models subcommands
    models_p = subparsers.add_parser("models", help="Model definitions management")
    models_sub = models_p.add_subparsers(dest="models_command")
    models_sub.add_parser("list", help="List available model definitions")
    show_model_p = models_sub.add_parser("show", help="Show model definition details")
    show_model_p.add_argument("name", help="Model name")

    # run - run a command with profile environment
    run_p = subparsers.add_parser("with", help="Run Claude with a profile")
    #run_p.add_argument("keyword", choices=["with"], help="Keyword 'with' to specify profile")
    run_p.add_argument("profile", help="Profile name")
    run_p.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to run (default: claude)")

    # install - copy built-in assets to user config
    install_p = subparsers.add_parser("install", help="Install built-in profiles and models to user config")
    install_p.add_argument("--force", "-f", action="store_true", help="Overwrite existing files")

    # secrets - manage secrets configuration
    secrets_p = subparsers.add_parser("secrets", help="Manage secrets configuration")
    secrets_sub = secrets_p.add_subparsers(dest="secrets_command")

    init_p = secrets_sub.add_parser("init", help="Initialize secrets template")
    init_p.add_argument("--generate", "-g", action="store_true", help="Generate random passwords")
    init_p.add_argument("--force", "-f", action="store_true", help="Overwrite existing secrets")

    secrets_sub.add_parser("path", help="Show secrets file path")
    secrets_sub.add_parser("export", help="Export secrets to .env file for docker compose")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    # Dispatch
    if args.command == "enter":
        return cmd_enter(args)
    elif args.command == "leave":
        return cmd_leave(args)
    elif args.command == "janitor":
        return cmd_janitor(args)
    elif args.command == "set-folder":
        return cmd_set_folder(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "env":
        return cmd_env(args)
    elif args.command == "proxy":
        return cmd_proxy(args)
    elif args.command == "db":
        return cmd_db(args)
    elif args.command == "profiles":
        return cmd_profiles(args)
    elif args.command == "models":
        return cmd_models(args)
    elif args.command == "with":
        return cmd_run(args)
    elif args.command == "install":
        return cmd_install(args)
    elif args.command == "secrets":
        return cmd_secrets(args)
    else:
        parser.print_help()
        return 1


def cmd_enter(args: argparse.Namespace) -> int:
    """Handle enter command."""
    from . import state, profiles, proxy

    debug = getattr(args, 'debug', False)
    token = args.token
    profile_name = args.profile
    directory = args.dir or os.getcwd()

    # Load profile
    profile = profiles.load_profile(profile_name, debug=debug)
    if profile is None:
        print(f"Error: Profile not found: {profile_name}", file=sys.stderr)
        return 1

    # Log profile selection and models
    print(f"[PROFILE_SELECTED] '{profile_name}' ({profile.meta.name})", file=sys.stderr)
    print(f"[MODELS_FOR_REGISTRATION] {len(profile.model_list)} models:", file=sys.stderr)
    for m in profile.model_list:
        print(f"  - {m.model_name}", file=sys.stderr)

    # Ensure proxy is running with profile's models
    model_defs = [m.to_dict() for m in profile.model_list]
    if not proxy.is_proxy_running():
        config_path = str(proxy.generate_litellm_config(model_defs=model_defs)) if model_defs else None
        if not proxy.start_proxy(config_path=config_path):
            print("Warning: Failed to start proxy", file=sys.stderr)
    elif model_defs:
        # Add any missing models via API (no restart needed)
        # Wait for recovery if proxy is not immediately healthy
        added, skipped = proxy.ensure_models(model_defs, debug=debug, wait_for_recovery=True)
        if debug and added > 0:
            print(f"Added {added} model(s) to proxy", file=sys.stderr)

    # Update state
    st = state.load_state()
    state.add_token(st, token, profile_name, directory)
    state.increment_models(st, profile.get_model_names())
    state.save_state(st)

    return 0


def cmd_leave(args: argparse.Namespace) -> int:
    """Handle leave command."""
    from . import state, profiles

    debug = getattr(args, 'debug', False)
    token = args.token

    st = state.load_state()
    token_info = state.get_token(st, token)

    if token_info is None:
        # Token not found, nothing to do
        return 0

    # Load profile to get model names
    profile = profiles.load_profile(token_info.profile, debug=debug)
    if profile:
        state.decrement_models(st, profile.get_model_names())

    state.remove_token(st, token)
    state.save_state(st)

    return 0


def cmd_janitor(args: argparse.Namespace) -> int:
    """Handle janitor command."""
    from . import state, proxy

    st = state.load_state()

    # Rate limit: only run once per minute unless forced
    if not args.force:
        if time.time() - st.last_janitor_run < 60:
            return 0

    st.last_janitor_run = time.time()

    # Find expired leases
    expired = state.get_expired_leases(st)

    if not expired:
        state.save_state(st)
        return 0

    # Delete expired models from proxy
    deleted = 0
    for model in expired:
        if proxy.delete_model(model):
            state.clear_lease(st, model)
            deleted += 1
            if not args.quiet:
                print(f"Deleted model: {model}")

    state.save_state(st)

    if not args.quiet and deleted > 0:
        print(f"Janitor: deleted {deleted} expired model(s)")

    return 0


def cmd_set_folder(args: argparse.Namespace) -> int:
    """Handle set-folder command."""
    from . import profiles

    debug = getattr(args, 'debug', False)
    profile_name = args.profile
    directory = Path(args.dir) if args.dir else Path.cwd()

    # Verify profile exists
    profile = profiles.load_profile(profile_name, debug=debug)
    if profile is None:
        print(f"Error: Profile not found: {profile_name}", file=sys.stderr)
        return 1

    # Generate token from canonical path
    canonical = directory.resolve()
    token = hashlib.sha256(str(canonical).encode()).hexdigest()[:16]

    envrc_path = directory / ".envrc"
    envrc_user_path = directory / ".envrc.user"
    gitignore_path = directory / ".gitignore"

    created_envrc = False

    # Create .envrc if missing
    if not envrc_path.exists():
        envrc_content = f'''# Claude Switch - Auto-generated
# Edit .envrc.user for customization (gitignored)

# Stable token for this directory
export AGENT_SHIM_TOKEN="{token}"

# Load user customizations
source_env_if_exists .envrc.user

# Apply shim configuration
if [[ -n "$AGENT_SHIM_PROFILE" ]]; then
    eval "$(run-claude env "$AGENT_SHIM_PROFILE" 2>/dev/null)"
fi
'''
        envrc_path.write_text(envrc_content)
        created_envrc = True
        print(f"Created: {envrc_path}")

    # Create/update .envrc.user
    envrc_user_content = f'''# Claude Switch User Config
# This file is gitignored - add your customizations here

export AGENT_SHIM_PROFILE="{profile_name}"

# Optional: Override specific models
# export ANTHROPIC_DEFAULT_OPUS_MODEL="custom-opus"

# Optional: Client-specific settings
# export AGENT_SHIM_CLIENT="claude"
'''
    envrc_user_path.write_text(envrc_user_content)
    print(f"Created: {envrc_user_path}")

    # Update .gitignore
    gitignore_entries = [".envrc.user"]
    if created_envrc:
        gitignore_entries.append(".envrc")

    if gitignore_path.exists():
        existing = gitignore_path.read_text()
        lines = existing.splitlines()
    else:
        existing = ""
        lines = []

    for entry in gitignore_entries:
        if entry not in lines:
            lines.append(entry)

    new_content = "\n".join(lines)
    if not new_content.endswith("\n"):
        new_content += "\n"

    if new_content != existing:
        gitignore_path.write_text(new_content)
        print(f"Updated: {gitignore_path}")

    print(f"\nProfile '{profile_name}' configured for {directory}")
    print("Run 'direnv allow' to activate")

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Handle status command."""
    from . import state, proxy, profiles

    st = state.load_state()
    proxy_status = proxy.get_status()

    print("=== Claude Switch Status ===")
    print()

    # Configuration files
    print("Configuration Files:")
    loaded = profiles.get_loaded_files()
    if loaded["profiles"]:
        for profile_file in loaded["profiles"]:
            print(f"  Profiles: {profile_file}")
    if loaded["models"]:
        for model_file in loaded["models"]:
            print(f"  Models: {model_file}")
    if not loaded["profiles"] and not loaded["models"]:
        print("  (none loaded)")
    print()

    # Proxy status
    print("Proxy:")
    if proxy_status.running:
        health = "healthy" if proxy_status.healthy else "unhealthy"
        print(f"  Status: running ({health})")
        print(f"  PID: {proxy_status.pid}")
        print(f"  URL: {proxy_status.url}")
        print(f"  Models: {proxy_status.model_count}")
    else:
        print("  Status: stopped")
    print()

    # Database container status
    print("Database Container:")
    if proxy_status.db_status:
        if not proxy_status.db_status.installed:
            print("  Infrastructure: not installed")
        elif not proxy_status.db_status.container_exists:
            print("  Container: not created")
        elif not proxy_status.db_status.running:
            print(f"  Status: stopped (ID: {proxy_status.db_status.container_id})")
        else:
            health = "healthy" if proxy_status.db_status.healthy else "starting"
            print(f"  Status: running ({health})")
            print(f"  Container ID: {proxy_status.db_status.container_id}")
    else:
        print("  Status: unknown")

    # Database connection status
    db_conn = "connected" if proxy_status.db_healthy else "disconnected"
    print(f"  Connection: {db_conn}")

    print()

    # Active tokens
    print("Active Tokens:")
    if st.active_tokens:
        for token, info in st.active_tokens.items():
            print(f"  {token[:8]}...: {info.profile} ({info.directory})")
    else:
        print("  (none)")

    print()

    # Model refcounts
    print("Model Refcounts:")
    if st.model_refcounts:
        for model, count in sorted(st.model_refcounts.items()):
            print(f"  {model}: {count}")
    else:
        print("  (none)")

    print()

    # Pending leases
    print("Pending Leases:")
    if st.model_leases:
        now = time.time()
        for model, delete_after in sorted(st.model_leases.items()):
            remaining = int(delete_after - now)
            if remaining > 0:
                print(f"  {model}: expires in {remaining}s")
            else:
                print(f"  {model}: expired (pending deletion)")
    else:
        print("  (none)")

    return 0


def cmd_env(args: argparse.Namespace) -> int:
    """Handle env command."""
    from . import profiles, proxy

    debug = getattr(args, 'debug', False)
    profile_name = args.profile

    profile = profiles.load_profile(profile_name, debug=debug)
    if profile is None:
        print(f"Error: Profile not found: {profile_name}", file=sys.stderr)
        return 1

    # Generate environment variables
    env_vars = {
        "ANTHROPIC_AUTH_TOKEN": proxy.get_api_key(),
        "ANTHROPIC_BASE_URL": proxy.get_proxy_url(),
        "API_TIMEOUT_MS": "3000000",
    }

    if profile.meta.haiku_model:
        env_vars["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = profile.meta.haiku_model
    if profile.meta.sonnet_model:
        env_vars["ANTHROPIC_DEFAULT_SONNET_MODEL"] = profile.meta.sonnet_model
    if profile.meta.opus_model:
        env_vars["ANTHROPIC_DEFAULT_OPUS_MODEL"] = profile.meta.opus_model

    # Output
    for key, value in env_vars.items():
        if args.export:
            print(f'export {key}="{value}"')
        else:
            print(f"{key}={value}")

    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Handle run command - execute a command with profile environment."""
    import subprocess
    from . import profiles, proxy

    debug = getattr(args, 'debug', False)
    profile_name = args.profile

    profile = profiles.load_profile(profile_name, debug=debug)
    if profile is None:
        print(f"Error: Profile not found: {profile_name}", file=sys.stderr)
        return 1

    # Log profile selection and models
    print(f"[PROFILE_SELECTED] '{profile_name}' ({profile.meta.name})", file=sys.stderr)
    print(f"[MODELS_FOR_REGISTRATION] {len(profile.model_list)} models:", file=sys.stderr)
    for m in profile.model_list:
        print(f"  - {m.model_name}", file=sys.stderr)

    # Verify profile has models resolved
    if not profile.model_list:
        print(f"Warning: Profile '{profile_name}' has no models resolved.", file=sys.stderr)
        print(f"  Check that model definitions exist for:", file=sys.stderr)
        if profile.meta.opus_model:
            print(f"    opus_model: {profile.meta.opus_model}", file=sys.stderr)
        if profile.meta.sonnet_model:
            print(f"    sonnet_model: {profile.meta.sonnet_model}", file=sys.stderr)
        if profile.meta.haiku_model:
            print(f"    haiku_model: {profile.meta.haiku_model}", file=sys.stderr)

    # Get model definitions for config generation
    model_defs = [m.to_dict() for m in profile.model_list]

    # Ensure proxy is running with profile's models
    if not proxy.is_proxy_running():
        # Start proxy with profile's models in config
        config_path = str(proxy.generate_litellm_config(model_defs=model_defs)) if model_defs else None
        if not proxy.start_proxy(config_path=config_path):
            print("Error: Failed to start proxy", file=sys.stderr)
            return 1
    else:
        # Proxy already running, add any missing models via API
        # Wait for recovery if proxy is not immediately healthy
        if model_defs:
            added, skipped = proxy.ensure_models(model_defs, debug=debug, wait_for_recovery=True)
            if debug and added > 0:
                print(f"Added {added} model(s) to proxy", file=sys.stderr)

    # Build environment
    env = os.environ.copy()
    env["ANTHROPIC_AUTH_TOKEN"] = proxy.get_api_key()
    env["ANTHROPIC_BASE_URL"] = proxy.get_proxy_url()
    env["API_TIMEOUT_MS"] = "3000000"

    if profile.meta.haiku_model:
        env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = profile.meta.haiku_model
    if profile.meta.sonnet_model:
        env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = profile.meta.sonnet_model
    if profile.meta.opus_model:
        env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = profile.meta.opus_model

    # Determine command to run
    cmd = args.cmd if args.cmd else ["claude"]

    cmd_status(args)

    # Execute
    try:
        result = subprocess.run(cmd, env=env)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


def cmd_proxy(args: argparse.Namespace) -> int:
    """Handle proxy commands."""
    from . import proxy

    debug = getattr(args, 'debug', False)

    if args.proxy_command == "start":
        # Start with empty model list, models are loaded on-demand via profiles
        no_db = getattr(args, 'no_db', False)
        if proxy.start_proxy(empty_config=True, no_db=no_db, debug=debug):
            print("Proxy started")
            return 0
        else:
            print("Failed to start proxy", file=sys.stderr)
            return 1

    elif args.proxy_command == "stop":
        # Stop proxy first
        if not proxy.stop_proxy():
            print("Failed to stop proxy", file=sys.stderr)
            return 1
        print("Proxy stopped")

        # Optionally stop database
        with_db = getattr(args, 'with_db', False)
        stop_all = getattr(args, 'all', False)

        if with_db or stop_all:
            print("Stopping database container...")
            if proxy.stop_db_container(remove=stop_all, debug=debug):
                if stop_all:
                    print("Database container removed")
                else:
                    print("Database container stopped")
            else:
                print("Failed to stop database container", file=sys.stderr)
                return 1

        return 0

    elif args.proxy_command == "status":
        status = proxy.get_status()

        # Proxy status
        print("Proxy:")
        if status.running:
            health = "healthy" if status.healthy else "unhealthy"
            print(f"  Status: running ({health})")
            print(f"  PID: {status.pid}")
            print(f"  URL: {status.url}")
            print(f"  Models: {status.model_count}")
        else:
            print("  Status: stopped")

        # Database container status
        print()
        print("Database Container:")
        if status.db_status:
            if not status.db_status.installed:
                print("  Infrastructure: not installed")
                print("  Run 'run-claude install' to install")
            elif not status.db_status.container_exists:
                print("  Container: not created")
            elif not status.db_status.running:
                print("  Container: stopped")
                print(f"  Container ID: {status.db_status.container_id}")
            else:
                health = "healthy" if status.db_status.healthy else "starting"
                print(f"  Container: running ({health})")
                print(f"  Container ID: {status.db_status.container_id}")

        # Database connection status
        db_conn = "connected" if status.db_healthy else "disconnected"
        print(f"  Connection: {db_conn}")

        return 0

    elif args.proxy_command == "health":
        if proxy.health_check():
            print("Healthy")
            return 0
        else:
            print("Unhealthy")
            return 1

    elif args.proxy_command == "db-test":
        if proxy.test_db_connection(debug=debug):
            print("Database connection: OK")
            return 0
        else:
            print("Database connection: FAILED")
            return 1

    else:
        print("Usage: run-claude proxy {start|stop|status|health|db-test}")
        return 1


def cmd_db(args: argparse.Namespace) -> int:
    """Handle database container commands."""
    from . import proxy

    debug = getattr(args, 'debug', False)

    if args.db_command == "start":
        # Ensure infrastructure is installed
        if not proxy.is_infrastructure_installed():
            print("Installing infrastructure...")
            if not proxy.install_infrastructure(debug=debug):
                print("Failed to install infrastructure", file=sys.stderr)
                return 1

        if proxy.start_db_container(wait=True, debug=debug):
            print("Database container started")
            return 0
        else:
            print("Failed to start database container", file=sys.stderr)
            return 1

    elif args.db_command == "stop":
        remove = getattr(args, 'remove', False)
        if proxy.stop_db_container(remove=remove, debug=debug):
            if remove:
                print("Database container removed")
            else:
                print("Database container stopped")
            return 0
        else:
            print("Failed to stop database container", file=sys.stderr)
            return 1

    elif args.db_command == "status":
        status = proxy.get_db_status()

        print("Database Container:")
        if not status.installed:
            print("  Infrastructure: not installed")
            print("  Run 'run-claude install' to install")
        elif not status.container_exists:
            print("  Container: not created")
            print("  Run 'run-claude db start' to create and start")
        elif not status.running:
            print("  Status: stopped")
            print(f"  Container ID: {status.container_id}")
        else:
            health = "healthy" if status.healthy else "starting"
            print(f"  Status: running ({health})")
            print(f"  Container ID: {status.container_id}")

        # Test actual connection
        print()
        print("Connection Test:")
        if proxy.test_db_connection(debug=debug):
            print("  Status: OK")
        else:
            print("  Status: FAILED")

        return 0

    else:
        print("Usage: run-claude db {start|stop|status}")
        return 1


def cmd_profiles(args: argparse.Namespace) -> int:
    """Handle profiles commands."""
    from . import profiles

    debug = getattr(args, 'debug', False)

    if args.profiles_command == "list":
        available = profiles.list_profiles(debug=debug)
        if available:
            print("Available profiles:")
            for name in available:
                print(f"  {name}")
        else:
            print("No profiles found")
        return 0

    elif args.profiles_command == "show":
        profile = profiles.load_profile(args.name, debug=debug)
        if profile is None:
            print(f"Profile not found: {args.name}", file=sys.stderr)
            return 1

        print(f"Profile: {profile.meta.name}")
        if profile.source_path:
            print(f"Loaded from: {profile.source_path}")

        # Also show model file sources
        loaded = profiles.get_loaded_files()
        if loaded["models"]:
            for model_file in loaded["models"]:
                print(f"Models loaded from: {model_file}")
        print()
        print("Model Aliases:")
        print(f"  opus:   {profile.meta.opus_model or '(not set)'}")
        print(f"  sonnet: {profile.meta.sonnet_model or '(not set)'}")
        print(f"  haiku:  {profile.meta.haiku_model or '(not set)'}")
        print()
        print("Models:")
        for model in profile.model_list:
            print(f"  - {model.model_name}")
        return 0

    elif args.profiles_command == "install":
        import shutil

        builtin_profiles = profiles.get_builtin_profiles_file()
        user_profiles = profiles.get_user_profiles_file()
        user_profiles.parent.mkdir(parents=True, exist_ok=True)

        if not builtin_profiles.exists():
            print("No built-in profiles found")
            return 0

        if user_profiles.exists():
            print(f"User profiles already exist: {user_profiles}")
            print("Use 'run-claude install --force' to overwrite")
            return 0

        shutil.copy2(builtin_profiles, user_profiles)
        print(f"Installed: {user_profiles}")
        return 0

    else:
        print("Usage: run-claude profiles {list|show|install}")
        return 1


def cmd_models(args: argparse.Namespace) -> int:
    """Handle models commands."""
    from . import profiles

    if args.models_command == "list":
        available = profiles.list_models()
        if available:
            print("Available model definitions:")
            for name in available:
                print(f"  {name}")
        else:
            print("No model definitions found")
        return 0

    elif args.models_command == "show":
        model_def = profiles.get_model_definition(args.name)
        if model_def is None:
            print(f"Model definition not found: {args.name}", file=sys.stderr)
            return 1

        print(f"Model: {model_def.model_name}")

        # Show model file sources
        loaded = profiles.get_loaded_files()
        if loaded["models"]:
            for model_file in loaded["models"]:
                print(f"Loaded from: {model_file}")
        print()
        print("LiteLLM Params:")
        for key, value in model_def.litellm_params.items():
            print(f"  {key}: {value}")
        return 0

    else:
        print("Usage: run-claude models {list|show}")
        return 1


def cmd_install(args: argparse.Namespace) -> int:
    """Install built-in profiles, models, and infrastructure to user directories."""
    import shutil
    from . import profiles, proxy

    debug = getattr(args, 'debug', False)
    config_dir = profiles.get_config_dir()
    user_profiles_file = profiles.get_user_profiles_file()
    user_models_file = profiles.get_user_models_file()
    builtin_profiles_file = profiles.get_builtin_profiles_file()
    builtin_models_file = profiles.get_builtin_models_file()

    # Create config directory
    config_dir.mkdir(parents=True, exist_ok=True)

    installed = 0
    skipped = 0

    # Copy models.yaml
    if builtin_models_file.exists():
        if not user_models_file.exists() or args.force:
            shutil.copy2(builtin_models_file, user_models_file)
            print(f"Installed: {user_models_file}")
            installed += 1
        else:
            print(f"Skipped (exists): {user_models_file}")
            skipped += 1

    # Copy profiles.yaml
    if builtin_profiles_file.exists():
        if not user_profiles_file.exists() or args.force:
            shutil.copy2(builtin_profiles_file, user_profiles_file)
            print(f"Installed: {user_profiles_file}")
            installed += 1
        else:
            print(f"Skipped (exists): {user_profiles_file}")
            skipped += 1

    # Install infrastructure (docker-compose files)
    dep_dir = proxy.get_dep_dir()
    if not proxy.is_infrastructure_installed() or args.force:
        if proxy.install_infrastructure(force=args.force, debug=debug):
            print(f"Installed: {dep_dir}/docker-compose.yaml")
            print(f"Installed: {dep_dir}/docker-compose.override.yaml")
            installed += 2
    else:
        print(f"Skipped (exists): {dep_dir}/docker-compose.yaml")
        skipped += 1

    print()
    print(f"Configuration installed to: {config_dir}")
    print(f"Infrastructure installed to: {dep_dir}")
    print(f"  {installed} file(s) installed")
    if skipped > 0:
        print(f"  {skipped} file(s) skipped (use --force to overwrite)")

    return 0


def cmd_secrets(args: argparse.Namespace) -> int:
    """Handle secrets commands."""
    from . import config

    debug = getattr(args, 'debug', False)

    if args.secrets_command == "init":
        generate = getattr(args, 'generate', False)
        force = getattr(args, 'force', False)
        config.ensure_secrets_template(force=force, generate_passwords=generate, debug=debug)
        return 0

    elif args.secrets_command == "path":
        secrets_file = config.get_secrets_file()
        print(str(secrets_file))
        return 0

    elif args.secrets_command == "export":
        try:
            env_file = config.export_env_file(debug=debug)
            print(f"Exported secrets to: {env_file}")
            print(f"\nSecrets automatically loaded by Docker Compose!")
            print(f"  cd dep && docker compose up -d")
            return 0
        except Exception:
            return 1

    else:
        print("Usage: run-claude secrets {init|path|export}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
