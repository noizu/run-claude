# web/ + helm/ — Landing Site

Elixir Hologram marketing site for **run-claude.therobotlives.com** (single route `/`).
Copy deck: `web/COPY.md` (sources of truth: README.md, profiles.yaml, CLAUDE.md, LICENSE).

```
web/
├── app/
│   ├── main_layout.ex         # Root HTML layout
│   └── pages/
│       ├── home_page.ex       # Landing page module
│       └── home_page.holo     # Hologram template
├── config/                    # Mix config (config.exs, runtime.exs, test.exs)
├── lib/
│   └── run_claude_web/        # OTP app: endpoint, router, health controller
├── priv/static/               # Compiled assets (CSS, hologram JS bundles)
├── test/                      # ExUnit tests
├── COPY.md                    # Landing copy deck (content source of truth)
├── Dockerfile                 # Release image build
├── mix.exs / mix.lock         # Elixir deps
└── .tool-versions             # Erlang/Elixir pins

helm/
└── run-claude-landing/        # Helm chart for the landing site
    ├── Chart.yaml
    ├── values.yaml
    └── templates/             # deployment, service, ingress, _helpers
```

Deploy: image built by CI from `web/Dockerfile`; chart rolls via ArgoCD on the
product remote's `main` (standard git-driven release path).

completions/
├── run-claude.bash            # Bash completion for the CLI
└── _run-claude                # Zsh completion
