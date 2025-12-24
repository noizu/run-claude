"""
Profile management for run-claude.

Loads and parses profile YAML files with model definitions.
Supports fall-through profile loading from multiple locations.

Profile search order (first match wins):
1. ~/.config/run-claude/user.profiles.yaml
2. ~/.config/run-claude/profiles.yaml
3. <install>/user.profiles.yaml
4. <install>/profiles.yaml

If a profile entry has `model: null` or `model: false`, it is treated
as not found and the search continues to the next file.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


_initialized = False


def ensure_initialized() -> None:
    """Ensure user config is initialized on first run."""
    global _initialized
    if _initialized:
        return
    _initialized = True

    config_dir = get_config_dir()
    marker = config_dir / ".initialized"

    if marker.exists():
        return

    # First run - copy built-in assets
    _do_first_run_init(config_dir, marker)


def _do_first_run_init(config_dir: Path, marker: Path) -> None:
    """Perform first-run initialization."""
    config_dir.mkdir(parents=True, exist_ok=True)

    builtin_profiles = get_builtin_profiles_file()
    builtin_models = get_builtin_models_file()

    installed = 0

    # Copy models.yaml
    if builtin_models.exists():
        dst = get_user_models_file()
        if not dst.exists():
            shutil.copy2(builtin_models, dst)
            installed += 1

    # Copy profiles.yaml (consolidated file)
    if builtin_profiles.exists():
        dst = get_user_profiles_file()
        if not dst.exists():
            shutil.copy2(builtin_profiles, dst)
            installed += 1

    # Create marker
    marker.touch()

    if installed > 0:
        print(f"run-claude: initialized {config_dir} ({installed} files)", file=sys.stderr)


def get_config_dir() -> Path:
    """Get XDG-compliant config directory."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        base = Path(xdg_config)
    else:
        base = Path.home() / ".config"
    return base / "run-claude"


def get_builtin_dir() -> Path:
    """Get built-in directory (shipped with tool)."""
    pkg_dir = Path(__file__).parent
    # When running from source, profiles.yaml is in parent directory
    if (pkg_dir.parent / "profiles.yaml").exists():
        return pkg_dir.parent
    # When installed via pip, profiles.yaml is inside the package
    return pkg_dir


def get_user_profiles_file() -> Path:
    """Get user profiles.yaml file path."""
    return get_config_dir() / "profiles.yaml"


def get_user_profiles_override_file() -> Path:
    """Get user.profiles.yaml file path (highest priority overrides)."""
    return get_config_dir() / "user.profiles.yaml"


def get_builtin_profiles_file() -> Path:
    """Get built-in profiles.yaml file path."""
    return get_builtin_dir() / "profiles.yaml"


def get_builtin_profiles_override_file() -> Path:
    """Get built-in user.profiles.yaml file path."""
    return get_builtin_dir() / "user.profiles.yaml"


def _get_profiles_files(debug: bool = False) -> list[Path]:
    """
    Get all profile files in priority order (highest to lowest).

    Search order (first match wins):
    1. User override: ~/.config/run-claude/user.profiles.yaml
    2. User config: ~/.config/run-claude/profiles.yaml
    3. Built-in override: <install>/user.profiles.yaml
    4. Built-in: <install>/profiles.yaml
    """
    files = []

    # User override (highest priority)
    user_override = get_user_profiles_override_file()
    if debug:
        print(f"DEBUG: User override profiles: {user_override} (exists={user_override.exists()})", file=sys.stderr)
    if user_override.exists():
        files.append(user_override)

    # User config
    user = get_user_profiles_file()
    if debug:
        print(f"DEBUG: User profiles: {user} (exists={user.exists()})", file=sys.stderr)
    if user.exists():
        files.append(user)

    # Built-in override
    builtin_override = get_builtin_profiles_override_file()
    if debug:
        print(f"DEBUG: Built-in override profiles: {builtin_override} (exists={builtin_override.exists()})", file=sys.stderr)
    if builtin_override.exists():
        files.append(builtin_override)

    # Built-in (lowest priority)
    builtin = get_builtin_profiles_file()
    if debug:
        print(f"DEBUG: Built-in profiles: {builtin} (exists={builtin.exists()})", file=sys.stderr)
    if builtin.exists():
        files.append(builtin)

    if debug:
        print(f"DEBUG: Profile files search order: {files}", file=sys.stderr)

    return files


def get_builtin_models_file() -> Path:
    """Get built-in models definitions file (shipped with tool)."""
    return Path(__file__).parent / "models.yaml"


def get_user_models_file() -> Path:
    """Get user models definitions file."""
    return get_config_dir() / "models.yaml"


def _find_models_files() -> list[Path]:
    """
    Find all models files in priority order (lowest to highest).

    Search order (later entries override earlier):
    1. Built-in: <package>/models.yaml
    2. User config: ~/.config/run-claude/models.yaml
    """
    files = []

    # Built-in (lowest priority)
    builtin = get_builtin_models_file()
    if builtin.exists():
        files.append(builtin)

    # User config (highest priority, overrides built-in)
    user = get_user_models_file()
    if user.exists():
        files.append(user)

    return files


@dataclass
class ModelDef:
    """LiteLLM model definition."""
    model_name: str
    litellm_params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "litellm_params": self.litellm_params,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelDef:
        return cls(
            model_name=data.get("model_name", ""),
            litellm_params=data.get("litellm_params", {}),
        )


@dataclass
class ProfileMeta:
    """Profile metadata."""
    name: str = ""
    opus_model: str = ""
    sonnet_model: str = ""
    haiku_model: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProfileMeta:
        return cls(
            name=data.get("name", ""),
            opus_model=data.get("opus_model", ""),
            sonnet_model=data.get("sonnet_model", ""),
            haiku_model=data.get("haiku_model", ""),
        )


@dataclass
class Profile:
    """Agent shim profile."""
    meta: ProfileMeta
    model_list: list[ModelDef] = field(default_factory=list)
    source_path: Path | None = None

    def get_model_names(self) -> list[str]:
        """Get list of model names in this profile."""
        return [m.model_name for m in self.model_list]

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": {
                "name": self.meta.name,
                "opus_model": self.meta.opus_model,
                "sonnet_model": self.meta.sonnet_model,
                "haiku_model": self.meta.haiku_model,
            },
            "model_list": [m.to_dict() for m in self.model_list],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], source_path: Path | None = None) -> Profile:
        meta = ProfileMeta.from_dict(data.get("meta", {}))
        model_list = [
            ModelDef.from_dict(m) for m in data.get("model_list", [])
        ]
        return cls(meta=meta, model_list=model_list, source_path=source_path)


# Cache for model definitions
_model_definitions_cache: dict[str, ModelDef] | None = None


def _require_yaml() -> None:
    """Raise error if PyYAML not installed."""
    if yaml is None:
        raise RuntimeError(
            "PyYAML is required for profile loading.\n"
            "Install with: pip install pyyaml"
        )


def load_model_definitions(force_reload: bool = False) -> dict[str, ModelDef]:
    """
    Load model definitions with base + user override logic.

    Returns a dict mapping model_name -> ModelDef.
    User definitions override base definitions.

    Search order (later entries override earlier):
    1. Built-in: <package>/models.yaml
    2. User config: ~/.config/run-claude/models.yaml
    """
    global _model_definitions_cache

    if _model_definitions_cache is not None and not force_reload:
        return _model_definitions_cache

    _require_yaml()

    models: dict[str, ModelDef] = {}

    # Load from all sources in priority order
    for models_file in _find_models_files():
        data = yaml.safe_load(models_file.read_text(encoding="utf-8")) or {}
        for model_data in data.get("model_list", []):
            model_def = ModelDef.from_dict(model_data)
            if model_def.model_name:
                models[model_def.model_name] = model_def

    _model_definitions_cache = models
    return models


def get_model_definition(model_name: str) -> ModelDef | None:
    """Get a specific model definition by name."""
    models = load_model_definitions()
    return models.get(model_name)


def resolve_profile_models(profile: Profile) -> list[ModelDef]:
    """
    Resolve profile model references to actual model definitions.

    Takes the model names from profile.meta (opus_model, sonnet_model, haiku_model)
    and resolves them to ModelDef objects from the model definitions.
    """
    models = load_model_definitions()
    resolved: list[ModelDef] = []
    seen: set[str] = set()

    # Collect unique model names from profile
    model_names = [
        profile.meta.opus_model,
        profile.meta.sonnet_model,
        profile.meta.haiku_model,
    ]

    for name in model_names:
        if name and name not in seen:
            seen.add(name)
            if name in models:
                resolved.append(models[name])

    return resolved


def _is_profile_disabled(profile_data: dict[str, Any] | None) -> bool:
    """
    Check if a profile entry is disabled (null/false model field).

    A profile is considered disabled if:
    - The profile_data is None, False, or empty
    - The 'model' field is explicitly null or false
    """
    if not profile_data:
        return True
    if profile_data is False:
        return True
    # Check for explicit model: null or model: false
    if "model" in profile_data:
        model_val = profile_data["model"]
        if model_val is None or model_val is False:
            return True
    return False


# Cache for loaded profiles files
_profiles_cache: dict[Path, dict[str, Any]] = {}


def _load_profiles_file(path: Path, debug: bool = False) -> dict[str, Any]:
    """Load and cache a profiles.yaml file."""
    if path in _profiles_cache:
        return _profiles_cache[path]

    _require_yaml()

    if debug:
        print(f"DEBUG: Loading profiles file: {path}", file=sys.stderr)

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        if debug:
            print(f"DEBUG: Error loading {path}: {e}", file=sys.stderr)
        data = {}

    _profiles_cache[path] = data
    return data


def load_profile(name: str, debug: bool = False) -> Profile | None:
    """
    Load a profile by name using fall-through logic.

    Search order (first match wins):
    1. ~/.config/run-claude/user.profiles.yaml
    2. ~/.config/run-claude/profiles.yaml
    3. <install>/user.profiles.yaml
    4. <install>/profiles.yaml

    If a profile entry has `model: null` or `model: false`, it is treated
    as not found and the search continues to the next file.

    After loading, resolves model references from model definitions.
    """
    _require_yaml()

    if debug:
        print(f"DEBUG: Loading profile '{name}'", file=sys.stderr)
        print(f"DEBUG: __file__ = {__file__}", file=sys.stderr)

    # Search through all profile files in priority order
    for profiles_file in _get_profiles_files(debug=debug):
        profiles_data = _load_profiles_file(profiles_file, debug=debug)

        if name in profiles_data:
            profile_data = profiles_data[name]

            if debug:
                print(f"DEBUG: Found '{name}' in {profiles_file}", file=sys.stderr)

            # Check if profile is disabled (null/false model)
            if _is_profile_disabled(profile_data):
                if debug:
                    print(f"DEBUG: Profile '{name}' is disabled in {profiles_file}, continuing search", file=sys.stderr)
                continue

            # Load the profile
            return _load_profile_from_data(name, profile_data, profiles_file, debug=debug)

    if debug:
        print(f"DEBUG: Profile '{name}' not found in any file", file=sys.stderr)
    return None


def _load_profile_from_data(
    name: str,
    data: dict[str, Any],
    source_path: Path,
    debug: bool = False
) -> Profile:
    """Create a Profile from parsed YAML data."""
    # Support both formats:
    # 1. New format with profile data directly under profile name
    # 2. Legacy format with 'meta' key

    if "meta" in data:
        meta_data = data["meta"]
    else:
        meta_data = data

    # Create ProfileMeta
    meta = ProfileMeta.from_dict(meta_data)

    # Use profile name as display name if not specified
    if not meta.name:
        meta.name = name

    profile = Profile(meta=meta, source_path=source_path)

    # Resolve model references to actual definitions
    profile.model_list = resolve_profile_models(profile)

    if debug:
        print(f"DEBUG: Loaded profile '{name}' from {source_path}", file=sys.stderr)

    return profile


def load_profile_file(path: Path) -> Profile:
    """
    Load a profile from a specific file path.

    Supports both:
    - Legacy single-profile files (one profile per file)
    - New consolidated format (must specify profile name)
    """
    _require_yaml()

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    profile = Profile.from_dict(data, source_path=path)

    # Use filename as name if not specified in meta
    if not profile.meta.name:
        profile.meta.name = path.stem

    # Resolve model references to actual definitions
    profile.model_list = resolve_profile_models(profile)

    return profile


def list_profiles(debug: bool = False) -> list[str]:
    """
    List all available profile names from all sources.

    Collects profile names from all profiles.yaml files, excluding
    disabled profiles (those with model: null or model: false).
    """
    profiles = set()

    for profiles_file in _get_profiles_files(debug=debug):
        if debug:
            print(f"DEBUG: Scanning {profiles_file} for profiles", file=sys.stderr)

        profiles_data = _load_profiles_file(profiles_file, debug=debug)

        for name, profile_data in profiles_data.items():
            # Skip disabled profiles
            if _is_profile_disabled(profile_data):
                if debug:
                    print(f"DEBUG: Skipping disabled profile: {name}", file=sys.stderr)
                continue

            if debug:
                print(f"DEBUG: Found profile: {name}", file=sys.stderr)
            profiles.add(name)

    if debug:
        print(f"DEBUG: Total profiles found: {len(profiles)}", file=sys.stderr)

    return sorted(profiles)


def list_models() -> list[str]:
    """List all available model names."""
    models = load_model_definitions()
    return sorted(models.keys())


def install_profile(name: str, profile_data: dict[str, Any]) -> Path:
    """
    Install or update a profile in user.profiles.yaml.

    Args:
        name: Profile name (key in the YAML file)
        profile_data: Profile data dictionary

    Returns:
        Path to the user.profiles.yaml file
    """
    _require_yaml()

    user_profiles_file = get_user_profiles_override_file()
    user_profiles_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing profiles or start fresh
    if user_profiles_file.exists():
        existing = yaml.safe_load(user_profiles_file.read_text(encoding="utf-8")) or {}
    else:
        existing = {}

    # Update with new profile
    existing[name] = profile_data

    # Write back
    user_profiles_file.write_text(
        yaml.safe_dump(existing, default_flow_style=False, allow_unicode=True),
        encoding="utf-8"
    )

    # Clear cache
    if user_profiles_file in _profiles_cache:
        del _profiles_cache[user_profiles_file]

    return user_profiles_file


def get_profile_path(name: str) -> Path | None:
    """
    Get the path to the profiles file containing a profile.

    Returns the first file that contains the profile (non-disabled).
    """
    for profiles_file in _get_profiles_files():
        profiles_data = _load_profiles_file(profiles_file)
        if name in profiles_data:
            profile_data = profiles_data[name]
            if not _is_profile_disabled(profile_data):
                return profiles_file

    return None
