# Test Health — run-claude
_Last measured: 2026-10-07 · branch develop@ae17255_

Two suites: the Python CLI (`tests/`, pytest) and the landing site (`web/test`, ExUnit/Hologram).
Before this change **neither suite ran in CI** — CI was docker smoke only — and both were red on develop
(stale assertions after intentional profile/copy changes).

| Metric | Before | After |
|---|---|---|
| CI PR wall-clock — critical path (warm / cold) | — / 88–108s (smoke only, always cold) | see PR #, filled from CI |
| Main release build (warm / cold) | never completes — `build-push` fails: REGISTRY_USER/PASSWORD secrets missing (every main push since ≥ 2026-09-09) | unchanged — owner-gated |
| CI acceptance test job (warm / cold) | not run | python-test / web-test, parallel to smoke |
| Local full-suite runtime (uptime load) | pytest 36s (load 45) · ExUnit 0.04s | same |
| Docker build (warm / cold) | 65–74s cold every run (gha cache never written) | smoke now exports `type=gha,scope=web,mode=max` |
| Tests in acceptance / slow tier | 0 in CI (170 py + 6 ex exist) | 175 + 1 strict-xfail / 0 |
| Async modules / total | ExUnit 0/1 (6 tests, 0.04s — not worth it) · pytest serial | unchanged |
| Coverage — acceptance pass | — | Python 40.2% · web 85.0% |
| Coverage — full pass | — | same (no slow tier) |
| Coverage gate | — | Python 35% (`--cov-fail-under`) · web 80% (`mix.exs` threshold) |

## Caching status
- GitHub Actions: deps ✅ (uv cache, mix deps+_build) · build ✅ · npm n.a. · .next/cache n.a. · PLT n.a. · develop-ref seeding ✅ (`push: develop` added; build-push/bump-chart remain main-only)
- Docker: buildx gha cache ✅ (smoke now writes it; was read-only and never seeded) · cache mounts ✅ (hex/rebar/deps; not persisted by gha exporter — Dockerfile re-runs deps.get) · .dockerignore ✅ (added) · release-cache warmer n.a. — the main run's smoke job seeds the main-ref cache before build-push, and a cold landing build is ~70s; a daily warmer costs more than it saves

## Slow tests (tier: nightly)
None. Slowest single test 3.1s (`test_zai_alt_profile_is_alias_of_zai_pro_alt`); whole pytest suite < 40s.

## Test debt
| Item | Kind | Notes |
|---|---|---|
| `test_inspect_zai_pro_instances` | stale assertion (fixed) | expected opus=glm-5.3-flash; bde56bd intentionally made zai-pro opus glm-5.3. Assertion updated. `profiles.yaml` header comment still says `opus = glm-5.3-flash` — doc drift, not changed here. |
| `web` landing test `claude-opus-4-8` | stale assertion (fixed) | #15 replaced the tier table ids with Claude 5 ids; asserts `claude-opus-5` now. |
| `web/config/test.exs` never imported | config gap (fixed) | `config.exs` only imported `runtime.exs`, so tests ran with `server: true` on :8150. Now imported for `:test`. |
| `HOLOGRAM_START=1` required for `mix test` | test seam | Hologram disables routing in :dev/:test without it; CI sets it. Locally: `HOLOGRAM_START=1 mix test`. |
| Committed `web/priv/static/hologram/page-*.js` bundle is stale | build artifact drift | a local compile emits a different page digest; Docker rebuilds it so prod is unaffected. |
| `test_inspect_cerebras_explicit_fable_tier` | xfail(strict) — real defect | CI-only failure: built-in `run_claude/models.yaml` lacks `cerebras/gemma-4-31b` (only `defaults/models.yaml` has it), so on a clean install the cerebras opus tier resolves with no `key_env`. Passed locally only because `~/.config/run-claude/models.yaml` masked it; test made hermetic. Fix = add the catalog entry, then drop the marker (strict xfail turns red when it passes). |
| Python coverage 40% | coverage gap | `litellm_proxy`, front-proxy, watchdog paths largely untested. |
| Release blocked | ops | `REGISTRY_USER` / `REGISTRY_PASSWORD` repo secrets missing — every `push: main` run is red. |

## Nightly
Not needed — no slow tier; total suite < 1 min.
