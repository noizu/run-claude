# PRD-04B3: Knowledge Base

**Phase**: 3 | **Est**: 2 days | **Repo**: npl-context (FastMCP)

## Context

Agents frequently need domain-specific knowledge (internal APIs, coding conventions, product specs) but lack a structured way to access it. This module provides file-based knowledge bases stored under `.claude/knowledge-base/` that are automatically surfaced when conversation topics match KB metadata.

## Goals (MVP)

1. File-based KB entries with YAML metadata (keywords, applicability, TOC)
2. Auto-detection: scan conversations, inject "KB Available: [title]" notifications
3. MCP tools for CRUD and search
4. DB-cached index for fast keyword matching

---

## FastMCP Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `create_kb_entry` | `title: str, content: str, keywords: list[str], applicability: dict?` | `{kb_id}` |
| `update_kb_entry` | `kb_id: str, content: str?, keywords: list[str]?, title: str?` | `{success}` |
| `list_kb_entries` | `keywords: list[str]?, limit: int = 20` | `list[KBSummary]` |
| `read_kb_entry` | `kb_id: str, section: str?` | `{title, content, metadata}` |
| `scan_kb_for_topic` | `topic: str` | `list[KBSummary]` |
| `delete_kb_entry` | `kb_id: str` | `{success}` |

## File Structure

```
.claude/knowledge-base/
├── index.yaml                  # Auto-generated global index
├── {kb_id}/
│   ├── README.md               # Main content with YAML frontmatter
│   └── attachments/            # Optional diagrams, code samples
│       └── example.py
```

### Entry Format

```markdown
---
kb_id: duet-lang-guide
title: Programming in the Duet Language
keywords: [duet, language, syntax, compiler, internal]
applicability:
  projects: [duet-compiler, duet-stdlib]
  tags: [programming, language-design]
  languages: [duet, python]
toc:
  - Basic Syntax
  - Type System
  - Concurrency Model
  - Standard Library
created: 2026-02-09
updated: 2026-02-09
author: engineering-team
---

# Programming in the Duet Language

## Basic Syntax
...
```

## Data Model

```sql
-- DB cache for fast keyword matching (source of truth is filesystem)
CREATE TABLE npl_kb_index (
    kb_id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(256) NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    applicability JSONB DEFAULT '{}',
    toc TEXT[],
    file_path TEXT NOT NULL,
    content_hash VARCHAR(64),  -- SHA256 of README.md for stale detection
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_kb_keywords ON npl_kb_index USING GIN(keywords);
```

## Hook Integration

**Pre-request hook** (`scan_for_kb`):

1. Extract keywords/topics from last 3-5 messages
2. Query `npl_kb_index` for keyword matches (GIN index, fast)
3. Check session metadata for already-notified KBs (avoid spam)
4. If new relevant KBs found, inject notification:
   ```
   [Knowledge Base Available: "Programming in the Duet Language"]
   Topics: Basic Syntax, Type System, Concurrency Model, Standard Library
   Use read_kb_entry("duet-lang-guide") to access, or request a sub-agent summary.
   ```
5. Track notified KBs in session metadata

**Index sync** (on server startup or tool call):
1. Walk `.claude/knowledge-base/` directories
2. Parse YAML frontmatter from each `README.md`
3. Upsert to `npl_kb_index` (compare `content_hash` for changes)

## Key Files

```
npl-context/src/npl_context/
├── tools/knowledge_base.py    # ~250 lines — KB CRUD tools
├── hooks/pre_request.py       # +100 lines — KB auto-detection
├── models/kb.py               # ~100 lines — KBEntry, KBSummary dataclasses
└── storage/fs.py              # ~200 lines — File system KB operations + index sync
```

## Future Phases

- Sub-agent KB summarizer (spawn agent to digest KB for specific question)
- Git-backed versioning
- KB templates (architecture doc, API spec, deployment guide)
- Web/TUI portal for browsing and editing
- Cross-repo KB sharing
- Automatic KB creation from conversations
