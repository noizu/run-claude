# Project Layout Summary

Quick reference tree of the project structure.

```
/github/infra/run-claude/
├── docs/                    # Documentation
│   ├── PROJ-ARCH.md
│   ├── PROJ-LAYOUT.md
│   ├── PRD-AUTO-INFRA.md
│   └── claude/
├── dep/                     # Infrastructure dependencies (Docker)
│   ├── docker-compose.yaml
│   ├── docker-compose.override.yaml
│   └── config/
├── dist/                    # Build output directory
├── hooks/                   # Shell integration hooks
├── playground/              # Test directories for validation
├── run_claude/              # Main Python package
│   └── callbacks/
├── scripts/                 # Utility scripts
├── templates/               # Template files for direnv
├── tests/                   # Test suite
├── .envrc                   # direnv configuration
├── .python-version          # Python version for runtime
├── .tool-versions           # asdf version manager config
├── Makefile                 # Build automation
├── profiles.yaml            # Profile definitions
├── pyproject.toml           # Python project configuration
├── uv.lock                  # Dependency lockfile
├── README.md                # User guide
├── SECRETS.md               # Secrets configuration guide
├── SECRETS_ADVANCED.md      # Advanced secrets management
├── SECRETS_QUICKSTART.md    # Quick reference for secrets
└── with-agent-shim          # Wrapper script for running with profiles
```