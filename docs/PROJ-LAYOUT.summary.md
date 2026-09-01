# Project Layout Summary

```
run-claude/
├── .claude/                 # Claude Code config (agents, commands, settings)
├── .github/                 # CI (workflows/ci.yml)
├── completions/             # Shell completions (bash, zsh)
├── dep/                     # Docker infrastructure (TimescaleDB, LiteLLM Dockerfile)
│   └── config/timescaledb/  #   DB init scripts
├── docs/                    # Documentation
│   ├── arch/                #   Architecture details (data-flows, design-patterns, infrastructure)
│   ├── claude/              #   Claude tool docs
│   ├── howto/               #   Task-oriented guides
│   ├── PRDs/                #   PRD series
│   └── layout/              #   Layout details (run-claude-package, docs, claude-config, web, repos)
├── helm/                    # Helm charts (run-claude-landing)
├── hooks/                   # Shell integration (bash/zsh hooks, installer)
├── playground/              # Test directories for profile switching
├── repos/                   # Gateway implementations (ex-litellm, go-litellm)
├── run_claude/              # Main Python package
│   ├── callbacks/           #   Provider compatibility layer
│   ├── defaults/            #   Built-in config files (models, profiles, hooks)
│   ├── hooks/               #   Lifecycle hook system (chain, loader, builtins)
│   ├── bin/go-litellm       #   Vendored Go gateway binary
│   ├── cli.py               #   CLI entry point
│   ├── chat.py              #   Interactive chat client
│   ├── config.py            #   Secrets and config management
│   ├── profiles.py          #   Profile loading with fallthrough
│   ├── proxy.py             #   LiteLLM proxy lifecycle
│   ├── front_proxy.py       #   Always-on reverse proxy (:4443)
│   ├── watchdog.py          #   Self-healing proxy watchdog daemon
│   ├── state.py             #   JSON state persistence
│   ├── keys.py              #   Named provider-key switching
│   ├── agent_runner.py      #   Agent execution wrapper
│   ├── litellm_proxy.py     #   LiteLLM proxy helpers
│   ├── opencode_cli.py      #   OpenCode CLI integration
│   └── models.yaml          #   Base model definitions
├── scripts/                 # Utility scripts (proxy runners)
├── templates/               # direnv templates
├── tests/                   # Test suite (cli, chat, callbacks, hooks, front proxy, watchdog, proxy)
├── web/                     # Landing site (Elixir Hologram)
├── CHANGELOG.md             # Release history
├── CLAUDE.md                # Claude Code project instructions
├── Makefile                 # Build automation
├── profiles.yaml            # Profile definitions
└── pyproject.toml           # Python project config
```
