# repos/ — Gateway Implementations

```
repos/
├── ex-litellm/              # Elixir LiteLLM port (Elixir app, own mix project)
│   ├── lib/ex_litellm/
│   │   ├── providers/       #   Per-provider adapters (anthropic, groq, zai, …)
│   │   ├── proxy/           #   Inference/auth/health/status plugs
│   │   ├── router/          #   Routing strategy + cooldown cache
│   │   ├── front_proxy/     #   Claude-facing front proxy (bootstrap, rules)
│   │   ├── schema/          #   Ecto schemas (repos, request logs)
│   │   └── anthropic/       #   Anthropic API translate + stream
│   ├── priv/repo/migrations/#   Ecto migrations (request_logs)
│   └── test/                #   ExUnit suites
└── go-litellm/              # Go gateway (git submodule; active release target)
    ├── cmd/go-litellm/      #   Entrypoint
    ├── internal/
    │   ├── gateway/         #   HTTP handlers, forwarding, key swap, status
    │   ├── providers/       #   Provider adapters (anthropic, groq, wafer, zai, …)
    │   ├── router/          #   Routing + strategy
    │   ├── anthropic/       #   Anthropic translate + stream
    │   ├── config/          #   YAML config loader
    │   └── keys/, store/    #   API-key management, persistence
    ├── config.example.stage.yaml  # Example gateway config
    └── Dockerfile, Makefile
```

`.gitmodules` registers `repos/litellm` (upstream LiteLLM fork) and
`repos/go-litellm`. `run_claude/bin/go-litellm` vendors the built Go binary.
