# PRD-04B4: Troubleshooting Guides

**Phase**: 3 | **Est**: 2 days | **Repo**: npl-context (FastMCP)

## Context

Agents repeatedly encounter the same errors (DB connection refused, auth failures, build errors). TSGs provide a structured way to detect known issues in conversation and surface resolution steps automatically.

## Goals (MVP)

1. TSG entries with error pattern metadata (substring/regex patterns)
2. Auto-detection: scan conversations for error patterns, inject TSG notification
3. Usage tracking (was the TSG helpful?)
4. MCP tools for CRUD and search

---

## FastMCP Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `create_tsg` | `title: str, content: str, patterns: list[str], applicability: dict?` | `{tsg_id}` |
| `update_tsg` | `tsg_id: str, content: str?, patterns: list[str]?` | `{success}` |
| `list_tsgs` | `limit: int = 20` | `list[TSGSummary]` |
| `read_tsg` | `tsg_id: str` | `{title, content, metadata}` |
| `scan_for_tsg` | `error_message: str, context: dict?` | `list[TSGSummary]` |
| `mark_tsg_helpful` | `tsg_id: str, resolved: bool` | `{success}` |

## File Structure

```
.claude/tsgs/
├── index.yaml
├── {tsg_id}/
│   └── README.md
```

### Entry Format

```markdown
---
tsg_id: db-connection-refused
title: PostgreSQL Connection Refused
patterns:
  - "connection refused"
  - "ECONNREFUSED"
  - "could not connect to server"
  - "pg_isready.*failed"
applicability:
  technologies: [postgresql, timescaledb]
severity: high
created: 2026-02-09
---

# PostgreSQL Connection Refused

## Symptoms
- `ECONNREFUSED 127.0.0.1:5432`
- `psycopg2.OperationalError: could not connect to server`

## Diagnosis
1. Check container: `docker ps | grep timescaledb`
2. Check port: `lsof -i :5433`
3. Check logs: `docker logs run-claude-timescaledb`

## Resolution
1. If container not running: `run-claude proxy start`
2. If port conflict: change port in `.env`
3. If container unhealthy: `docker compose restart timescaledb`
```

## Data Model

```sql
CREATE TABLE npl_tsg_index (
    tsg_id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(256) NOT NULL,
    patterns TEXT[] DEFAULT '{}',
    applicability JSONB DEFAULT '{}',
    severity VARCHAR(16),
    file_path TEXT NOT NULL,
    content_hash VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_tsg_patterns ON npl_tsg_index USING GIN(patterns);

CREATE TABLE npl_tsg_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tsg_id VARCHAR(64) REFERENCES npl_tsg_index(tsg_id),
    session_id VARCHAR(64) NOT NULL,
    matched_pattern TEXT,
    resolved BOOLEAN,
    used_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Hook Integration

**Pre-request hook** (`detect_tsgs`):

1. Scan last 3 messages for error-like content (stack traces, error keywords)
2. For each potential error, query `npl_tsg_index` patterns (substring match)
3. If TSG matches and not already surfaced in session:
   ```
   [Troubleshooting Guide Available: "PostgreSQL Connection Refused"]
   Matched pattern: "connection refused"
   Use read_tsg("db-connection-refused") for resolution steps.
   ```
4. Log usage in `npl_tsg_usage`

## Key Files

```
npl-context/src/npl_context/
├── tools/tsg.py               # ~300 lines
├── hooks/pre_request.py       # +150 lines — Pattern scanning
├── models/tsg.py              # ~120 lines
└── storage/fs.py              # +100 lines — TSG file ops + index sync
```

## Future Phases

- Regex pattern matching
- TSG success rate analytics
- Auto-TSG creation from resolved issues
- Severity-based priority injection
- TUI/web management interface
