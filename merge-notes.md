# merge-notes — run-claude (sep-1 branch sweep, 2026-09-01)

CLI wrapper repo (noizu/run-claude). **Base chosen: `main` @ fadcad5 (2026-09-01,
freshest).** `sep-1` tag landed on main tip fadcad5. `develop` exists on origin but
is behind main (stale side); local develop synced ff to origin/develop.

## Review/merge sequence
1. **PR #4 — `epic/site-deploy` → `develop`** (landing site da27526 + deploy wiring
   8f17b0e). models.yaml conflicts resolved with branch side (content already shipped
   on main via da27526).
2. After #4 lands, consider syncing `develop` up to `main` (main also carries
   afe7dcd/3bce0d3 go-litellm fixes develop lacks). PRing develop→main is the
   eventual path; not done here (main untouched per sweep rules).

## Skip/ignore list
- `chore/remove-site` (L+R @ bde16db): fully merged into `main`, but NOT into
  `develop`, and semantically contradicts PR #4 (it deletes `web/`, the epic ships
  deploy wiring for it). Excluded from the epic; kept alive. Safe to delete once
  develop syncs with main.
- `mono-repo-dev` DIVERGED local da23143 / remote abfb4a3 (stale 08-31 snapshot):
  left untouched per rules.
- `origin/extension` @ f1f2df0 (2026-04-21, remote-only): untouched, unmerged.
- Local-only `feat/deploy-wiring` deleted (contained in epic/site-deploy).

## Open PRs
| # | Branch | Base | What |
|---|--------|------|------|
| 4 | epic/site-deploy | develop | Landing site + Dockerfile/workflow/helm deploy wiring |
