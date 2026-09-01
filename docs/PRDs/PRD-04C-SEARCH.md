# PRD-04C: Extended Search

**Phase**: 4 | **Est**: 3 days | **Repo**: npl-context (FastMCP)

## Context

Once all messages flow through the proxy with lifecycle hooks, we can track and index them for later search. This enables queries like "find how secret management was configured by Sandy-132 sub-agent" with filters by repo, agent, tags, and time range.

## Goals (MVP)

1. Log all request/response messages to TimescaleDB hypertable
2. Capture metadata: repo, agent, sub-agent type, tags, objective
3. Keyword search with metadata filters
4. Basic semantic search via pg_trgm (defer pgvector to future)
5. Summary generation from search results

---

## FastMCP Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `search_message_history` | `query: str, repo: str?, agent: str?, tags: list[str]?, start_date: str?, end_date: str?, limit: int` | `list[SearchResult]` |
| `summarize_search_results` | `query: str, results: list[SearchResult]?, focus: str?` | `{summary: str}` |
| `get_message_detail` | `message_id: int` | `{full message + metadata}` |
| `list_agents` | `repo: str?` | `list[AgentInfo]` |
| `list_repos` | `` | `list[RepoInfo]` |

## Data Model

```sql
-- TimescaleDB hypertable for time-series optimization
CREATE TABLE message_history (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    request_id TEXT,
    model TEXT,
    profile TEXT,
    directory TEXT,
    repo_url TEXT,
    agent_name TEXT,
    sub_agent_type TEXT,
    objective TEXT,
    tags TEXT[],
    messages JSONB,
    response JSONB,
    tokens_input INT,
    tokens_output INT,
    cost_usd DECIMAL(10,6),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
SELECT create_hypertable('message_history', 'timestamp');

CREATE INDEX idx_mh_repo ON message_history(repo_url);
CREATE INDEX idx_mh_agent ON message_history(agent_name);
CREATE INDEX idx_mh_tags ON message_history USING GIN(tags);
-- pg_trgm for keyword search
CREATE INDEX idx_mh_messages_trgm ON message_history USING GIN(
    (messages::text) gin_trgm_ops
);
```

## Hook Integration

**Post-response hook** (`track_message`):

1. Extract metadata from request context:
   - `repo_url`: from `RUN_CLAUDE_REPO_URL` env or git remote
   - `agent_name`: from request metadata or `RUN_CLAUDE_AGENT_NAME`
   - `sub_agent_type`: from metadata
   - `tags`: from session active tags
   - `objective`: from session metadata
2. Extract token usage and estimate cost from response
3. INSERT into `message_history`

**Metadata extraction**: Git remote URL, agent name, and objective are passed through request metadata headers or inferred from environment.

## Search Implementation

**Keyword search**: Use pg_trgm `%` operator for fuzzy matching on message content.

```sql
SELECT * FROM message_history
WHERE messages::text % $query
  AND ($repo IS NULL OR repo_url = $repo)
  AND ($agent IS NULL OR agent_name = $agent)
  AND ($tags IS NULL OR tags @> $tags)
  AND timestamp BETWEEN $start AND $end
ORDER BY similarity(messages::text, $query) DESC
LIMIT $limit;
```

**Summary generation**: Pass top-N results to a summarization prompt via the proxy itself.

## Key Files

```
npl-context/src/npl_context/
├── tools/search.py            # ~250 lines — Search + summary tools
├── hooks/post_response.py     # +200 lines — Message tracking
├── models/search.py           # ~100 lines — SearchResult, AgentInfo dataclasses
└── storage/db.py              # +200 lines — Search queries + hypertable ops
```

## Future Phases

- pgvector embeddings for true semantic search
- Cross-session conversation tracking
- Export to training datasets (links to 4d.3)
- Rich report generation (markdown, HTML)
- Search result visualization
