# PRD-06: Documentation

**Phase**: 6 | **Est**: 3 days | **Repo**: run-claude

## Context

Current docs are decent (README, SECRETS guides, PROJ-ARCH/LAYOUT) but inline docstrings are sparse, CLI help text lacks examples, no man pages exist, and documentation isn't deployed to a web platform.

## Goals (MVP)

1. Google-style docstrings for all public functions
2. Enhanced `--help` with examples and common workflows
3. Man pages via help2man
4. Sphinx + ReadTheDocs deployment

---

## 6a: Inline Docstrings

### Target Format (Google style)

```python
def load_profile(name: str) -> Profile:
    """Load a profile with multi-file fallthrough.

    Searches in priority order:
    1. ~/.config/run-claude/user.profiles.yaml
    2. ~/.config/run-claude/profiles.yaml
    3. <package>/profiles.yaml

    Args:
        name: Profile name (e.g., "anthropic", "groq").

    Returns:
        Profile with metadata and resolved model definitions.

    Raises:
        ValueError: If profile not found in any source.

    Example:
        >>> profile = load_profile("anthropic")
        >>> print(profile.meta.opus_model)
        claude-opus-4-20250514
    """
```

### Files to Document

| File | Public functions | Priority |
|------|-----------------|----------|
| `profiles.py` | `load_profile`, `list_profiles`, `resolve_profile_models`, `hydrate_model_def` | High |
| `proxy.py` | `start_proxy`, `stop_proxy`, `health_check`, `add_model`, `delete_model`, `ensure_models` | High |
| `config.py` | `load_secrets`, `create_secrets_template`, `export_env_file`, `load_env_file` | High |
| `state.py` | `load_state`, `save_state`, `increment_models`, `decrement_models` | Medium |
| `cli.py` | `cmd_*` handlers | Medium |

## 6b: Enhanced CLI Help

### Modified File: `run_claude/cli.py`

```python
parser = argparse.ArgumentParser(
    prog="run-claude",
    description="Directory-aware AI model routing via LiteLLM proxy.",
    epilog="""
Common workflows:

  First-time setup:
    run-claude install && run-claude secrets init
    $EDITOR ~/.config/run-claude/.secrets
    run-claude secrets export && run-claude proxy start

  Configure a project:
    cd ~/my-project && run-claude set-folder anthropic

  Quick run without direnv:
    run-claude with anthropic -- claude-code "analyze this"
""",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
```

Each subcommand gets epilog with examples.

## 6c: Man Pages

### Build Process

```makefile
# Makefile addition
man:
	mkdir -p docs/man
	help2man -N -n "directory-aware AI model routing" \
	  -o docs/man/run-claude.1 run-claude

install-man:
	install -Dm644 docs/man/run-claude.1 \
	  $(HOME)/.local/share/man/man1/run-claude.1
```

### Distribution

Include in wheel via hatch config:
```toml
[tool.hatch.build.targets.wheel.force-include]
"docs/man/run-claude.1" = "share/man/man1/run-claude.1"
```

## 6d: ReadTheDocs

### New Files

```
docs/
├── conf.py                 # Sphinx config
├── index.rst               # Landing page
├── getting-started.rst     # Quick start
├── installation.rst        # Install guide
├── profiles.rst            # Profile system
├── models.rst              # Model definitions
├── cli-reference.rst       # CLI commands
├── architecture.rst        # System architecture
├── api/                    # Auto-generated
│   ├── profiles.rst
│   ├── proxy.rst
│   ├── state.rst
│   └── config.rst
└── requirements.txt        # sphinx, sphinx-rtd-theme

.readthedocs.yaml           # Build config
```

### `.readthedocs.yaml`

```yaml
version: 2
build:
  os: ubuntu-22.04
  tools:
    python: "3.11"
sphinx:
  configuration: docs/conf.py
  fail_on_warning: true
python:
  install:
    - method: pip
      path: .
    - requirements: docs/requirements.txt
```

### Makefile Addition

```makefile
docs:
	cd docs && sphinx-build -b html . _build/html

docs-serve:
	python -m http.server 8000 -d docs/_build/html
```

## Key Files to Create/Modify

| File | Action |
|------|--------|
| `run_claude/profiles.py` | Add docstrings |
| `run_claude/proxy.py` | Add docstrings |
| `run_claude/config.py` | Add docstrings |
| `run_claude/state.py` | Add docstrings |
| `run_claude/cli.py` | Enhance help text |
| `docs/conf.py` | New: Sphinx config |
| `docs/*.rst` | New: Documentation pages |
| `.readthedocs.yaml` | New: Build config |
| `Makefile` | Add docs/man targets |
