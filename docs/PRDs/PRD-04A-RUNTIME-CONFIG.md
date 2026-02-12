# PRD-04A: Runtime Config Tweaks

**Phase**: 3 | **Est**: 2 days | **Repo**: npl-context (FastMCP)

## Context

Agents may need to switch models mid-session (e.g., Cerebras for speed-sensitive tasks), tweak hyper-parameters, set cost constraints, or inject system messages. Currently, model selection is static per-profile. This adds dynamic runtime control via MCP tools.

## Goals (MVP)

1. MCP tools to add/modify model entries at runtime
2. Session-level hyper-parameter overrides (temperature, max_tokens)
3. Cost tracking and per-session cost limits
4. System message injection via hooks

---

## FastMCP Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `add_model` | `model_name: str, provider: str, model_id: str, api_key_env: str?, api_base: str?, hyper_params: dict?` | `{success, model_id}` |
| `modify_model` | `model_name: str, hyper_params: dict` | `{success}` |
| `list_models` | `tier: str?` (opus/sonnet/haiku/all) | `list[ModelInfo]` |
| `set_cost_limit` | `session_id: str, limit_usd: float` | `{success}` |
| `inject_system_message` | `session_id: str, message: str, position: str` (prepend/append) | `{success}` |
| `get_session_cost` | `session_id: str` | `{spent_usd, limit_usd, remaining}` |

## Data Model

```sql
CREATE TABLE npl_session_models (
    session_id VARCHAR(64) PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    custom_models JSONB DEFAULT '{}',
    hyper_overrides JSONB DEFAULT '{}',
    cost_limit_usd DECIMAL(10,4),
    spent_usd DECIMAL(10,4) DEFAULT 0
);

CREATE TABLE npl_system_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(64) NOT NULL,
    message TEXT NOT NULL,
    position VARCHAR(16) CHECK (position IN ('prepend', 'append')),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_sysmsg_session ON npl_system_messages(session_id, active);
```

## Hook Integration

**Pre-request hook:**
1. Extract session_id from request metadata
2. Query session overrides (custom models, hyper-params)
3. Query system messages for injection
4. Modify request: swap model, set params, inject messages
5. Check cost limit → reject if exceeded

**Post-response hook:**
1. Extract token usage, estimate cost
2. Update `spent_usd` in session
3. Log warning if approaching limit

## Key Files

```
npl-context/src/npl_context/
├── tools/model_config.py    # ~200 lines — MCP tool implementations
├── hooks/pre_request.py     # +150 lines — Model/param/message override logic
├── hooks/post_response.py   # +100 lines — Cost tracking
└── models/session.py        # ~80 lines — SessionConfig, SystemMessage dataclasses
```

## Future Phases

- Multi-model fallback chains (primary → fallback1 → fallback2)
- Cost alerting (webhooks at 80%/100% thresholds)
- Model performance analytics (latency, error rates)
- Per-user quotas
- Repo-local profile overrides (`.claude/models.yaml`)
