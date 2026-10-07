# run-claude model explorer

Standalone Next.js app that browses run-claude's model registry and profiles —
search models & profiles, filter by provider, and dig from a profile's tier
slots down to full model cards (pricing, token limits, thinking support,
estimated throughput) shown as modal popups.

## What it reads

The app mirrors `run_claude/profiles.py` resolution logic exactly:

- **Models** — `run_claude/models.yaml` (installation) first, then
  `~/.config/run-claude/models.yaml` (user override) which replaces entries by
  `model_name`; an override without its own description inherits the previous
  entry's metadata. Family clones (`zai/…` → `zai-alt/…`, `zai-oa/…` →
  `zai-oa-alt/…`) are synthesized for missing destinations.
- **Profiles** — 4-tier first-match-wins chain:
  `~/.config/run-claude/user.profiles.yaml` → `~/.config/run-claude/profiles.yaml`
  → `<repo>/user.profiles.yaml` → `<repo>/profiles.yaml`. A `model: null`
  entry is treated as disabled and the search falls through.
  The `fable` slot falls back to `opus` when unset; `ultra`/`fast`/`cheap`
  are always included.

Files are re-read on every request (`force-dynamic`), so edits to either the
installation or the user-override YAML show up on refresh — no rebuild needed.

## Attribute provenance

Model pricing/throughput metadata carries a `source` badge:

| Badge | Meaning |
|---|---|
| documented pricing | found in provider docs/press at enrichment time |
| inferred | derived from a sibling model or provider convention |
| estimated | reasoned estimate (all `tokens_per_second` values are estimates) |
| subscription/plan | billed via subscription quota; list prices shown for reference |
| free | $0 (local, free tiers) |

Enriched values live in `run_claude/models.yaml` under `metadata.pricing`,
`metadata.limits`, `metadata.thinking`, `metadata.context_window`,
`metadata.modalities` (input/output: text/image/audio/video),
`metadata.supports_tools`, and `metadata.tokens_per_second`.

## Run

Preferred — via the CLI, which serves the app, opens a browser tab, and shuts
the server down cleanly on Ctrl-C / Ctrl-D:

```bash
run-claude explorer                 # http://localhost:3312
run-claude explorer --port 3400     # custom port
run-claude explorer --dev           # Next.js dev server (HMR)
run-claude explorer --no-open       # don't open a browser tab
```

First run performs `npm install` + `npm run build` automatically. If the port
is already serving an explorer, the CLI just opens a tab instead of spawning a
second server.

Or directly:

```bash
cd model-explorer
npm install
npm run dev        # http://localhost:3312
```

Environment overrides:

| Variable | Default | Purpose |
|---|---|---|
| `RUN_CLAUDE_REPO_ROOT` | auto-detected (walk-up to `run_claude/models.yaml`) | installation files location |
| `RUN_CLAUDE_CONFIG_DIR` | `$XDG_CONFIG_HOME/run-claude` or `~/.config/run-claude` | user override files location |

Secrets (`api_key` / `api_key_name`) in `litellm_params` are never sent to the
client — only the model string, api base, and reasoning effort are displayed.
