# docs/ — Documentation

Project documentation, architecture references, and PRDs.

```
docs/
├── PROJ-ARCH.md             # Architecture overview
├── PROJ-ARCH.summary.md     # Architecture quick reference
├── PROJ-LAYOUT.md           # Project structure guide (this system)
├── PROJ-LAYOUT.summary.md   # Layout quick reference
├── PRD-AUTO-INFRA.md        # Auto-infrastructure PRD
├── arch/                    # Extracted architecture details
│   ├── data-flows.md        #   Request/response flow diagrams
│   ├── design-patterns.md   #   Key design patterns
│   └── infrastructure.md    #   Network, env vars, security
├── layout/                  # Extracted layout details
│   ├── run-claude-package.md#   Main package breakdown
│   └── docs.md              #   This file
├── PRDs/                    # Product requirement documents
│   ├── PRD-00-META.md       #   Meta PRD (index/overview)
│   ├── PRD-01-ENV-SETUP.md  #   Environment setup
│   ├── PRD-02-CONTAINERIZE.md
│   ├── PRD-03-HOOKS.md      #   Hook system PRD
│   ├── PRD-04A through 04D3 #   Runtime config, context, behavior
│   ├── PRD-05-TUI.md        #   Terminal UI
│   ├── PRD-06-DOCS.md       #   Documentation
│   ├── PRD-07-RC-WEBSITE.md #   run-claude website
│   └── PRD-08-NPL-WEBSITE.md#   NPL website
└── claude/                  # Claude AI integration docs
    ├── tools.md             #   Tool specifications
    ├── tools.summary.md     #   Quick reference
    └── tools/               #   Per-category tool docs (8 pairs)
```
