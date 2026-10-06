# Threat Model Summary

Single-user workstation tool. Loopback-only gateway (:4443) holding provider keys and
persisted OAuth headers; no public ingress for the core tool (only the static landing
site is deployed). Crown jewels: `.secrets`/`.env` (0600), `front-proxy-auth-state.json`,
and the eval'd shell-hook environment.

## Register counts

10 entries: 2 mitigated/accepted-by-design · 3 partial · 2 open · 3 accepted.

## Open items

- **T-001 (Medium, Spoofing/EoP)**: hardcoded fallback master key `sk-litellm-master-key-12345` (`proxy.py:79`) when no `LITELLM_MASTER_KEY` configured — any local process can drive the gateway API. Mitigate by setting `LITELLM_MASTER_KEY` in `.secrets`.
- **T-002 (Medium, Info disclosure)**: `front-proxy-auth-state.json` persists upstream auth headers plaintext with no `chmod 0600` (unlike `.secrets`/`.env`).

## Notable partials

- T-003 request-log.jsonl metadata logs (override `RUN_CLAUDE_REQUEST_LOG`; no prompt bodies on success path)
- T-008 provider keys transited via process env (inherent to env hydration)
- T-009 vendored go-litellm binary has no hash verification vs pinned submodule source

## Accepted

Local-process trust baseline (eval of `run-claude env` output T-004, dynamic hook imports T-005); loopback DB `sslmode=disable` (T-006); no gateway rate limiting (T-007); minimal audit trail (T-010).

## Controls verified in code

- `.secrets` + `.env` chmod 0600 (`config.py`)
- All listeners bind 127.0.0.1 (`proxy.py`, `front_proxy.py`)
- No key values in YAML — `os.environ/VAR` refs resolved at load
- Atomic auth-state writes (tmp + replace)
