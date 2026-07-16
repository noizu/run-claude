# Changelog — utilities/agent/run-claude

## [Unreleased]
- Restructured `docs/` for the per-level NPL arch/layout doc convention: rewrote `PROJ-ARCH.md`/`PROJ-LAYOUT.md` and their summaries, refreshed `docs/layout/run-claude-package.md` (ff72b3565bf, 2026-07-16)
- Added `docs/PROJ-HOWTO.md` + summary + `docs/howto/` extractions: task-oriented guides for install/setup, provider switching, secrets, watchdog lifecycle, model/profile customization, and stuck-state troubleshooting (2026-07-17)
- Added `docs/PROJ-FAQ.md` + summary: motivation/fit/comparison/capability/caveat/trust Q&A cross-linked to PROJ-HOWTO and PROJ-ARCH (2026-07-17)

## [m4-proxy-logging-and-model-refresh] — 2026-07-09 — tag: `utilities-agent-run-claude/m4-proxy-logging-and-model-refresh`
Milestone summary: hardened proxy logging so it never breaks CLI commands and never leaks credentials, and refreshed the default Claude model lineup.

### Added
- Sensitive-key redaction for proxy logs: `SENSITIVE_LOG_KEYS` matching plus URL-credential scrubbing, covered by `tests/test_proxy_logging.py`
- Optional httpx/httpcore debug logging via `RUN_CLAUDE_HTTPX_LOG_FILE` with safe fallback candidates

### Changed
- Proxy log destination now prefers the XDG state dir (`proxy.log`), falling back to `/var/log` only when writable; logging failures can no longer prevent `run-claude proxy status` from importing
- Default Anthropic profiles bumped: `claude-opus-4-6` → `claude-opus-4-8`, `claude-sonnet-4-6` → `claude-sonnet-5` (incl. `[1m]` variants); matching `models.yaml` entries added
- Pinned nodejs `24.18.0` in `.tool-versions`

## [m3-front-proxy-hardening] — 2026-06-27 — tag: `utilities-agent-run-claude/m3-front-proxy-hardening`
Milestone summary: turned the front proxy (:4443) into a first-class auth/bootstrap layer and broadened multi-provider profile coverage.

### Added
- Front-proxy auth handling: `FILL_ME_IN` placeholder substitution, persisted auth state (`front-proxy-auth-state.json`), and JSONL request logging (`tests/test_front_proxy.py`)
- `/bootstrap` endpoint for the Claude CLI: serves available models from LiteLLM `model/info` as `additional_model_options`, merged with local model definitions
- New provider profiles: OpenAI GPT-5.5/5.4, ZAI GLM-5.x, Cerebras GLM, Groq (compound, qwen3-32b, gpt-oss-120b), Grok 4.3, DeepSeek v4 — with ~230 new `models.yaml` entries

### Changed
- Shell hooks (`bash_hook.sh`, `zsh_hook.zsh`) and CLI wiring updated for the new front-proxy flow

## [m2-watchdog-and-model-catalog] — 2026-06-20 — tag: `utilities-agent-run-claude/m2-watchdog-and-model-catalog`
Milestone summary: made the proxy pair self-healing and overhauled the model catalog.

### Added
- Self-healing watchdog daemon (`watchdog.py`, ~300 lines + tests): detached setsid process keeping both the front proxy (:4443) and LiteLLM proxy (:4444) alive; intentional stops recorded via a `stop.marker` sentinel so deliberate `proxy stop` is never undone; re-spawned idempotently by `proxy start` and the shell-hook `enter`
- `run-claude proxy` CLI subcommands and state-dir helpers supporting the watchdog lifecycle

### Changed
- Major `models.yaml` refresh (~250 changed lines) plus updated packaged defaults

## [m1-initial-landing] — 2026-06-14 — tag: `utilities-agent-run-claude/m1-initial-landing`
Milestone summary: the run-claude package lands whole (~16.8k lines) — a multi-provider agent-runner toolkit that fronts Claude Code (and OpenCode) with a local proxy stack.

### Added
- `run_claude` Python package: CLI (`cli.py`), front proxy (`front_proxy.py`, :4443), LiteLLM proxy manager (`proxy.py`/`litellm_proxy.py`, :4444), profile system (`profiles.py`, `profiles.yaml`, packaged defaults), model catalogs (`models.yaml`, ~1300-line default), provider-compat callbacks, hook chain loader/builtins, state management, `agent_runner.py`, `opencode_cli.py`
- Shell integration: `hooks/bash_hook.sh`, `hooks/zsh_hook.zsh`, `hooks/install.sh`; `with-agent-shim` launcher; `scripts/run-litellm-*`
- `dep/` docker-compose stack (LiteLLM + TimescaleDB) and envrc templates
- Docs suite (`docs/PROJ-ARCH*`, `PROJ-LAYOUT*`, arch/ and layout/ subdocs, `PRD-AUTO-INFRA.md`), README, SECRETS guides (quickstart/advanced), CLAUDE.md, Makefile
- Playground projects per provider (cerebras, groq, local, multi) and test suites (`test_cli`, `test_hooks`, `test_callbacks`)
