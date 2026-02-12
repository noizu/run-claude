# PRD-04B2: Synthetic Memory

**Phase**: 4 | **Est**: 3 days | **Repo**: npl-context (FastMCP)

## Context

Current LLM memory systems (Claude's built-in, MEMORY.md files) are limited: flat key-value stores, no decay, no relevance scoring, no cross-session persistence with smart injection. This module provides a richer memory system with context-aware injection, temporal decay, and relevance weighting.

## Goals (MVP)

1. Store memories with context (project, tags, related memories)
2. Scan incoming messages for keyword/tag matches
3. Inject matched memories with decay: full → digest → stub
4. Tag memories as relevant/irrelevant to adjust persistence and recall

---

## FastMCP Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `store_memory` | `content: str, tags: list[str], context: dict?, related_ids: list[str]?` | `{memory_id}` |
| `recall_memories` | `query: str, tags: list[str]?, limit: int = 10` | `list[Memory]` |
| `tag_memory_relevant` | `memory_id: str, objective: str, relevance: float (0-1), reason: str` | `{success}` |
| `tag_memory_irrelevant` | `memory_id: str, reason: str` | `{success}` |
| `update_memory` | `memory_id: str, content: str?, tags: list[str]?` | `{success}` |
| `list_memories` | `tags: list[str]?, status: str?` | `list[Memory]` |
| `delete_memory` | `memory_id: str` | `{success}` |

## Data Model

```sql
CREATE TABLE npl_memories (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    digest TEXT,  -- 1-2 sentence summary (generated on store or first decay)
    context JSONB DEFAULT '{}',  -- {project, agent, observations}
    tags TEXT[] DEFAULT '{}',
    related_ids UUID[] DEFAULT '{}',
    view_mode VARCHAR(16) DEFAULT 'full',  -- full, digest, stub
    relevance_boost FLOAT DEFAULT 0.0,  -- Accumulated from tag_relevant calls
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    access_count INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE
);
CREATE INDEX idx_memories_tags ON npl_memories USING GIN(tags);
CREATE INDEX idx_memories_active ON npl_memories(active, last_accessed);

CREATE TABLE npl_memory_relevance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID REFERENCES npl_memories(memory_id),
    objective VARCHAR(256) NOT NULL,
    relevance_score FLOAT CHECK (relevance_score BETWEEN 0 AND 1),
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_rel_memory ON npl_memory_relevance(memory_id);

CREATE TABLE npl_memory_injections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID REFERENCES npl_memories(memory_id),
    session_id VARCHAR(64) NOT NULL,
    view_mode VARCHAR(16) NOT NULL,
    injected_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_inj_session ON npl_memory_injections(session_id);
```

## Decay Rules

```
Injection count in session | View mode
--------------------------+----------
1-3                        | full
4-10                       | digest (1-2 sentence summary)
10+                        | stub ("Memory available: {title}")
```

Additional factors:
- `tag_memory_relevant()` → resets decay counter, boosts future recall weight
- `tag_memory_irrelevant()` → immediate collapse to stub or skip
- Age: memories older than 7 days without access decay faster
- `relevance_boost > 0.8` → never auto-collapse

## Hook Integration

**Pre-request hook** (`inject_memories`):

1. Extract keywords from last N messages (simple: split + stop word removal)
2. Extract active tags from session metadata
3. Query memories: `WHERE active = TRUE AND (tags && $active_tags OR content ILIKE $keyword)`
4. For each matched memory:
   a. Check injection history for this session
   b. Determine view_mode based on injection count + relevance_boost
   c. Format injection payload:
      - **full**: `[Memory: {title}]\n{content}`
      - **digest**: `[Memory: {title}] {digest}`
      - **stub**: `[Memory available: {title} — use recall_memories for details]`
5. Inject as system messages before user's last message
6. Update `last_accessed`, `access_count`, log to `npl_memory_injections`

## Key Files

```
npl-context/src/npl_context/
├── tools/memory.py            # ~300 lines — Memory CRUD tools
├── hooks/pre_request.py       # +200 lines — Memory scanning and injection
├── models/memory.py           # ~120 lines — Memory, Relevance dataclasses
└── storage/db.py              # +150 lines — Memory queries
```

## Future Phases

- Vector embedding search via pgvector
- Automatic memory extraction from conversations (detect interesting facts)
- Memory graph visualization (related memories as network)
- Agent mood/emotional context tracking
- Memory clustering by topic
- Cross-project memory sharing
