# Project Layout Summary

```
run-claude/
├── .claude/                 # Claude Code config (agents, commands, settings)
├── docs/                    # Documentation
│   ├── arch/                #   Architecture details (data-flows, design-patterns, infrastructure)
│   ├── layout/              #   Layout details (run-claude-package, docs)
│   ├── PRDs/                #   Product requirement documents
│   └── claude/              #   Claude AI tool specifications
├── dep/                     # Docker infrastructure (TimescaleDB, LiteLLM Dockerfile)
├── hooks/                   # Shell integration (bash/zsh hooks, installer)
├── playground/              # Test directories for profile switching
├── run_claude/              # Main Python package
│   ├── callbacks/           #   Provider compatibility layer
│   ├── hooks/               #   Lifecycle hook system (chain, loader, builtins)
│   ├── cli.py               #   CLI entry point
│   ├── config.py            #   Secrets and config management
│   ├── profiles.py          #   Profile loading with fallthrough
│   ├── proxy.py             #   LiteLLM proxy lifecycle
│   ├── state.py             #   JSON state persistence
│   └── models.yaml          #   Built-in model definitions
├── scripts/                 # Utility scripts (proxy runners)
├── templates/               # direnv templates
├── tests/                   # Test suite (cli, callbacks, hooks)
├── CLAUDE.md                # Claude Code project instructions
├── Makefile                 # Build automation
├── profiles.yaml            # Built-in profile definitions
└── pyproject.toml           # Python project config
```
