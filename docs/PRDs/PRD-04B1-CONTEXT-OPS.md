# PRD-04B1: Context Manipulation

**Phase**: 4 | **Est**: 4 days | **Repo**: npl-context (FastMCP)

## Context

LLM chat threads grow unbounded. Irrelevant messages waste tokens and degrade model performance. This module lets agents (and operators) restructure chat threads in-flight: tagging, summarizing, reordering, and splicing messages before they reach the provider.

## Goals (MVP)

1. Tag messages with metadata for filtering
2. Digest (collapse) message ranges into summaries
3. Revise (replace) message sequences with alternatives
4. Snip (remove) message sequences
5. Resequence (reorder) messages
6. Insert synthetic messages
7. All operations reversible

---

## Operations

### Tag
Associate string tags with message ranges. Tags are used by other operations (digest, revise) to conditionally apply.

```
tag_messages(session_id, range=[5,10], tags=["database-design"])
```

### Digest
Replace a range of messages with a single summary message.

```
digest_messages(session_id, range=[3,8], summary="Discussed auth options; chose JWT")
→ Messages 3-8 replaced with: [system: "Discussed auth options; chose JWT"]
```

### Revise
Replace a sequence with alternative messages. Tracked via UUID. Expand/collapse supported.

```
revise_messages(session_id, range=[5,10], replacements=[
    {"role": "user", "content": "Refined question about auth"},
    {"role": "assistant", "content": "Here's the JWT implementation..."}
])
→ Messages 5-10 replaced with 2 alt messages
→ Expand marker before, collapse marker after
```

### Snip
Remove messages completely. Special case of revise with empty replacements.

```
snip_messages(session_id, range=[5,8])
→ Messages 5-8 removed
→ Single expand/collapse marker inserted
```

### Resequence
Reorder messages for better comprehension. Tagged as resequence for apply/revert.

```
resequence_messages(session_id, new_order=[8,9,5,6,7,10,11])
→ Messages reordered in specified sequence
→ apply/revert switch available
```

### Insert
Insert synthetic messages at a position. Fancy revise with original messages preserved.

```
insert_messages(session_id, after=5, messages=[
    {"role": "assistant", "content": "(Context: user later clarified they meant PostgreSQL)"}
])
→ New message inserted between 5 and 6
```

---

## FastMCP Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `tag_messages` | `session_id, start_idx, end_idx, tags: list[str]` | `{success, tag_count}` |
| `digest_messages` | `session_id, start_idx, end_idx, summary: str` | `{operation_id}` |
| `revise_messages` | `session_id, start_idx, end_idx, replacements: list[dict]` | `{operation_id}` |
| `snip_messages` | `session_id, start_idx, end_idx` | `{operation_id}` |
| `resequence_messages` | `session_id, new_order: list[int]` | `{operation_id}` |
| `insert_messages` | `session_id, after_idx: int, messages: list[dict]` | `{operation_id}` |
| `list_operations` | `session_id, active_only: bool` | `list[Operation]` |
| `revert_operation` | `operation_id: str` | `{success}` |
| `toggle_operation` | `operation_id: str, active: bool` | `{success}` |

## Data Model

```sql
CREATE TABLE npl_message_digests (
    digest VARCHAR(64) PRIMARY KEY,  -- SHA256 of role+content
    session_id VARCHAR(64) NOT NULL,
    message_idx INT NOT NULL,
    role VARCHAR(16) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_digests_session ON npl_message_digests(session_id, message_idx);

CREATE TABLE npl_message_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(64) NOT NULL,
    start_idx INT NOT NULL,
    end_idx INT NOT NULL,
    tag VARCHAR(128) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_tags_session ON npl_message_tags(session_id);
CREATE INDEX idx_tags_tag ON npl_message_tags(tag);

CREATE TABLE npl_operations (
    operation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(64) NOT NULL,
    op_type VARCHAR(32) NOT NULL,  -- digest, revise, snip, resequence, insert
    original_range INT[] NOT NULL,
    replacement_data JSONB,  -- New messages, summary, or new_order
    active BOOLEAN DEFAULT TRUE,
    tags TEXT[],  -- Conditional: only apply when these tags active
    created_at TIMESTAMPTZ DEFAULT NOW(),
    reverted_at TIMESTAMPTZ
);
CREATE INDEX idx_ops_session ON npl_operations(session_id, active);
```

## Hook Integration

**Pre-request hook** (`apply_context_operations`):

1. Compute SHA256 digest for each message → store/update in `npl_message_digests`
2. Query `npl_operations` WHERE `session_id` AND `active = TRUE`
3. Filter by tag conditions (only apply if operation's tags match current active tags)
4. Sort operations by `original_range[0]` descending (apply from end to avoid index shift)
5. For each operation:
   - **digest**: Replace `messages[start:end+1]` with `[{"role": "system", "content": summary}]`
   - **revise**: Replace `messages[start:end+1]` with `replacement_data`
   - **snip**: Remove `messages[start:end+1]`
   - **resequence**: Reorder entire array per `new_order`
   - **insert**: Splice `replacement_data` after `after_idx`
6. Return modified messages array

**Important**: Operations are applied in reverse index order to prevent index shifting issues.

## Key Files

```
npl-context/src/npl_context/
├── tools/context_ops.py       # ~400 lines — All manipulation tools
├── hooks/pre_request.py       # +200 lines — Operation application engine
├── models/message.py          # ~150 lines — Operation, MessageDigest dataclasses
└── storage/db.py              # +150 lines — Operation CRUD queries
```

## Future Phases

- Conditional operations by tag/objective (auto-inferred from conversation)
- TUI operator interface for visual thread editing
- Expand/collapse markers (prefix/suffix tracking messages)
- Automatic relevance scoring via embeddings
- Nested operations (revise within a digest)
