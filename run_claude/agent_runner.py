"""Shared agent runner logic for Claude and OpenCode."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable


class AgentConfig:
    """Configuration for which agent to run."""

    def __init__(self, agent_name: str, default_cmd: list[str], env_vars_fn: Callable):
        """
        Args:
            agent_name: 'claude' or 'opencode'
            default_cmd: Default command to run (e.g., ['claude'] or ['opencode'])
            env_vars_fn: Function that takes profile and proxy info and returns dict of env vars
        """
        self.agent_name = agent_name
        self.default_cmd = default_cmd
        self.env_vars_fn = env_vars_fn


def build_env_vars_anthropic(profile, proxy_url: str, api_key: str) -> dict[str, str]:
    """Build environment variables for Anthropic API."""
    from .front_proxy import DEFAULT_PORT as FRONT_PROXY_PORT
    env = {}
    env["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{FRONT_PROXY_PORT}"
    env["API_TIMEOUT_MS"] = "3000000"

    if profile.meta.haiku_model:
        env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = profile.meta.haiku_model
    if profile.meta.sonnet_model:
        env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = profile.meta.sonnet_model
    if profile.meta.opus_model:
        env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = profile.meta.opus_model
    fable_model = profile.meta.effective_fable_model()
    if fable_model:
        env["ANTHROPIC_DEFAULT_FABLE_MODEL"] = fable_model
        # Claude Code assumes a 200k window for catalog-unknown model IDs; the
        # run-claude catalog knows the real one, so pass it through unless the
        # user already pinned it.
        if not os.environ.get("CLAUDE_CODE_MAX_CONTEXT_TOKENS"):
            window = _catalog_context_window(fable_model)
            if window:
                env["CLAUDE_CODE_MAX_CONTEXT_TOKENS"] = str(window)

    return env


def _catalog_context_window(model_name: str) -> int | None:
    """context_window for a model from the catalog (models.yaml), if known."""
    try:
        from .profiles import load_model_definitions
        model_def = load_model_definitions().get(model_name)
        if model_def and model_def.metadata.context_window:
            return model_def.metadata.context_window
    except Exception:
        pass
    return None


# Built-in Claude Code model IDs -> profile slot. Claude Code >= 2.1.2xx ships a long
# built-in model list; selecting one of these sends the real `claude-*` ID, which
# bypasses ANTHROPIC_DEFAULT_*_MODEL and the front proxy forwards to api.anthropic.com.
# `modelOverrides` rewrites them to the profile's slot model. Add new CLI IDs here.
BUILTIN_CLAUDE_MODEL_SLOTS: dict[str, str] = {
    "claude-fable-5-1": "fable",
    "claude-fable-5": "fable",
    "claude-opus-5-5": "opus",
    "claude-opus-5-1": "opus",
    "claude-opus-5": "opus",
    "claude-opus-4-8": "opus",
    "claude-sonnet-5-5": "sonnet",
    "claude-sonnet-5": "sonnet",
    "claude-sonnet-4-6": "sonnet",
    "claude-sonnet-4-5": "sonnet",
    "claude-haiku-4-5": "haiku",
    "claude-haiku-4-5-20251001": "haiku",
}


def build_model_overrides(profile) -> dict[str, str]:
    """Map built-in claude-* IDs to the profile's slot models.

    Slots whose profile model is itself a real `claude-*` ID (e.g. the anthropic
    profile) are left alone so they keep passing through to Anthropic.
    """
    slot_ids = {**BUILTIN_CLAUDE_MODEL_SLOTS, **_extra_builtin_slots()}
    overrides: dict[str, str] = {}
    for model_id, slot in slot_ids.items():
        target = profile.meta.slot_model(slot)
        if not target or target.startswith("claude-"):
            continue
        overrides[model_id] = target
        overrides[f"{model_id}[1m]"] = target
    return overrides


def build_model_picker_options(profile) -> list[dict[str, str]]:
    """modelPicker option rows for the profile's models that declare behavesAs.

    Claude Code warns "isn't described by this version's model catalog" for
    gateway model IDs it doesn't know; a `behavesAs` full model ID (v2.1.257+)
    on the picker row gives it the mapped model's capabilities and context
    assumptions. Rows are additive (replaceBuiltInOptions stays false).
    """
    try:
        from .profiles import load_model_definitions
        model_defs = load_model_definitions()
    except Exception:
        return []
    names = {profile.meta.slot_model(slot) for slot in ("fable", "opus", "sonnet", "haiku")}
    names |= {m for m in (profile.meta.extended or []) if m}
    rows = []
    for name in sorted(names):
        model_def = model_defs.get(name)
        behaves_as = model_def.metadata.behaves_as if model_def else ""
        if behaves_as:
            rows.append({"model": name, "behavesAs": behaves_as})
    return rows


def model_overrides_enabled() -> bool:
    """modelOverrides injection is opt-in: set RUN_CLAUDE_MODEL_OVERRIDES=1.

    Default is off so launches use only the ANTHROPIC_DEFAULT_*_MODEL env vars.
    """
    return os.environ.get("RUN_CLAUDE_MODEL_OVERRIDES", "").strip().lower() in ("1", "true", "yes", "on")


def _extra_builtin_slots() -> dict[str, str]:
    """Extra built-in IDs from RUN_CLAUDE_EXTRA_BUILTIN_IDS="id=slot,id=slot".

    Lets a newly shipped Claude Code model ID be remapped immediately, without
    waiting for a run-claude release to extend BUILTIN_CLAUDE_MODEL_SLOTS.
    """
    extra: dict[str, str] = {}
    for item in os.environ.get("RUN_CLAUDE_EXTRA_BUILTIN_IDS", "").split(","):
        model_id, _, slot = item.strip().partition("=")
        if model_id and slot in ("fable", "opus", "sonnet", "haiku"):
            extra[model_id] = slot
    return extra


def _split_user_settings(cmd: list[str]) -> tuple[list[str], dict | None]:
    """Remove the user's first --settings arg; return (rest, parsed settings or None).

    Accepts inline JSON or a file path. Raises ValueError if it can't be parsed.
    """
    import json

    for i, arg in enumerate(cmd):
        if arg == "--settings" and i + 1 < len(cmd):
            value, rest = cmd[i + 1], cmd[:i] + cmd[i + 2:]
        elif arg.startswith("--settings="):
            value, rest = arg.split("=", 1)[1], cmd[:i] + cmd[i + 1:]
        else:
            continue
        text = value if value.lstrip().startswith("{") else Path(value).expanduser().read_text()
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("--settings must be a JSON object")
        return rest, data
    return cmd, None


def inject_model_overrides(cmd: list[str], profile, profile_name: str) -> list[str]:
    """Add per-launch `--settings '<inline json>'` carrying modelOverrides to claude.

    Nothing is written to disk. A user-supplied --settings (inline or file) is
    merged: its other keys are kept and its own modelOverrides entries win.
    """
    import json

    if not cmd or Path(cmd[0]).name != "claude":
        return cmd
    overrides = build_model_overrides(profile)
    if not overrides:
        return cmd
    try:
        rest, user_settings = _split_user_settings(cmd[1:])
    except (OSError, ValueError) as e:
        print(f"[MODEL_OVERRIDES] WARNING: cannot merge your --settings ({e}); "
              "built-in claude-* IDs may leak to api.anthropic.com for this launch",
              file=sys.stderr)
        return cmd
    merged = dict(user_settings or {})
    merged["modelOverrides"] = {**overrides, **(merged.get("modelOverrides") or {})}
    picker_rows = build_model_picker_options(profile)
    if picker_rows:
        user_picker = merged.get("modelPicker") or {}
        if not isinstance(user_picker, dict):
            user_picker = {}
        options = [o for o in (user_picker.get("options") or []) if isinstance(o, dict)]
        seen = {o.get("model") for o in options}
        options += [row for row in picker_rows if row["model"] not in seen]
        merged["modelPicker"] = {**user_picker, "options": options}
    print(f"[MODEL_OVERRIDES] {len(merged['modelOverrides'])} entries "
          f"(profile {profile_name}{', merged with --settings' if user_settings else ''})"
          f"{f', {len(picker_rows)} modelPicker rows' if picker_rows else ''}",
          file=sys.stderr)
    return [cmd[0], "--settings", json.dumps(merged, separators=(",", ":")), *rest]


def build_env_vars_openai(profile, proxy_url: str, api_key: str) -> dict[str, str]:
    """Build environment variables for OpenAI-compatible API."""
    env = {}
    env["OPENAI_API_KEY"] = api_key
    env["OPENAI_BASE_URL"] = proxy_url

    return env


def cmd_run_agent(
    args: argparse.Namespace,
    agent_config: AgentConfig,
    debug: bool = False,
) -> int:
    """Run an agent with profile environment.

    Args:
        args: Parsed arguments (must have 'profile' and 'cmd' attributes)
        agent_config: AgentConfig specifying which agent to run
        debug: Enable debug output

    Returns:
        Exit code from subprocess
    """
    from . import profiles, proxy

    # argparse.REMAINDER absorbs --refresh into args.cmd; extract it manually
    refresh = getattr(args, 'refresh', False)
    if hasattr(args, 'cmd') and '--refresh' in args.cmd:
        args.cmd = [a for a in args.cmd if a != '--refresh']
        refresh = True

    profile_name = args.profile

    if refresh:
        print("[REFRESH] Clearing model/profile caches", file=sys.stderr)
        profiles.clear_caches()

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
        if profile.meta.effective_fable_model():
            print(f"    fable_model: {profile.meta.effective_fable_model()}", file=sys.stderr)

    # Get model definitions for config generation
    model_defs = [m.to_dict() for m in profile.model_list]

    # Ensure proxy is running with profile's models
    # start_proxy handles: stale PIDs, unhealthy state, and retries on transient failures
    config_path = str(proxy.generate_litellm_config(model_defs=model_defs)) if model_defs else None
    if not proxy.start_proxy(config_path=config_path, debug=debug):
        print("Error: Failed to start proxy after retries", file=sys.stderr)
        log_lines = proxy.tail_proxy_log(20)
        if log_lines:
            print("  Recent proxy log output:", file=sys.stderr)
            for line in log_lines:
                print(f"    {line}", file=sys.stderr)
        else:
            print(f"  No log output found at {proxy.get_log_file()}", file=sys.stderr)
        return 1

    # Proxy is running and healthy — ensure models are registered
    if model_defs:
        added, skipped, failed = proxy.ensure_models(model_defs, debug=debug, wait_for_recovery=True, force=refresh)
        if debug and added > 0:
            print(f"Added {added} model(s) to proxy", file=sys.stderr)
        if failed > 0 and added == 0 and skipped == 0:
            print(f"Error: All {failed} model(s) failed to register", file=sys.stderr)
            return 1

    # Build environment
    env = os.environ.copy()

    # Claude Code prefers ANTHROPIC_API_KEY over its own OAuth/subscription login
    # when the variable is set. A stale key inherited from the shell would
    # silently switch auth mode and bypass the profile's proxy credentials, so
    # drop it before launch.
    if agent_config.agent_name == "claude" and env.pop("ANTHROPIC_API_KEY", None) is not None:
        print("[ENV] Unset inherited ANTHROPIC_API_KEY before launching claude", file=sys.stderr)

    # Add agent-specific environment variables
    proxy_url = proxy.get_proxy_url()
    api_key = proxy.get_api_key()
    agent_env = agent_config.env_vars_fn(profile, proxy_url, api_key)
    env.update(agent_env)

    # Determine command to run
    cmd = args.cmd if args.cmd else agent_config.default_cmd
    if agent_config.agent_name == "claude" and model_overrides_enabled():
        cmd = inject_model_overrides(list(cmd), profile, profile_name)

    # Print status (reuse existing function if needed)
    from . import state
    st = state.load_state()
    proxy_status = proxy.get_status()

    print(f"\n=== {agent_config.agent_name.capitalize()} Agent Status ===", file=sys.stderr)
    if proxy_status.running:
        health = "healthy" if proxy_status.healthy else "unhealthy"
        print(
            f"Proxy: {proxy_status.implementation} running ({health}) - {proxy_status.url}",
            file=sys.stderr,
        )
        print(f"Models: {proxy_status.model_count}", file=sys.stderr)
    print(f"Profile: {profile_name} ({profile.meta.name})", file=sys.stderr)
    print(f"Command: {' '.join(cmd)}\n", file=sys.stderr)

    # Execute
    try:
        result = subprocess.run(cmd, env=env)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
