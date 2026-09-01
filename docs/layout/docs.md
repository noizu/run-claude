# docs/ — Documentation

Project documentation, architecture references, and PRDs.

```
docs/
├── PROJ-ARCH.md             # Architecture overview
├── PROJ-ARCH.summary.md     # Architecture quick reference
├── PROJ-LAYOUT.md           # Project structure guide (this system)
├── PROJ-LAYOUT.summary.md   # Layout quick reference
├── PROJ-FAQ.md              # Frequently asked questions
├── PROJ-FAQ.summary.md      # FAQ quick reference
├── PROJ-HOWTO.md            # How-to index
├── PROJ-HOWTO.summary.md    # How-to quick reference
├── PRD-AUTO-INFRA.md        # Auto-infrastructure PRD
├── arch/                    # Extracted architecture details
│   ├── data-flows.md        #   Request/response flow diagrams
│   ├── design-patterns.md   #   Key design patterns
│   └── infrastructure.md    #   Network, env vars, security
├── claude/                  # Claude-specific tool docs
│   ├── tools.md             #   Tool suite overview (+ summary)
│   └── tools/               #   Per-domain docs (agents, file-ops, search, …)
├── howto/                   # Task-oriented guides
│   ├── customize-models-and-profiles.md
│   ├── manage-secrets.md
│   ├── troubleshoot-stuck-state.md
│   ├── use-claude-plan-passthrough.md
│   └── watchdog-and-proxy-lifecycle.md
├── PRDs/                    # PRD series (00-meta … 08-npl-website)
└── layout/                  # Extracted layout details
    ├── run-claude-package.md #   Main package breakdown
    ├── docs.md              #   This file
    ├── claude-config.md     #   .claude/ directory details
    ├── web.md               #   web/ + helm/ landing-site details
    └── repos.md             #   Gateway repos (ex-litellm, go-litellm)
```
