# PRD-04D3: Fine-Tuning Datasets

**Phase**: 5 | **Est**: 2 days | **Repo**: npl-context (FastMCP)

## Context

When agents produce exceptional output (or learn from mistakes), those interactions are valuable training data. This module extracts, cleans, and exports fine-tuning datasets from message history, tagged by quality flags from the eval system.

## Goals (MVP)

1. Extract high-quality sequences from message history (eval_score >= threshold)
2. Create revised sequence pairs (bad output → corrected output)
3. Auto-tag by agent type, domain, NPL conventions
4. Export JSONL compatible with OpenAI/Anthropic fine-tuning APIs

---

## FastMCP Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `prepare_dataset` | `quality_threshold: float, tags: list[str]?, start_date: str?, end_date: str?, max_examples: int` | `{count, export_path, stats}` |
| `link_revision_pair` | `original_id: int, revised_id: int, notes: str` | `{success}` |
| `export_dataset` | `dataset_path: str, provider: str (openai/anthropic/jsonl)` | `{output_path}` |
| `review_candidates` | `limit: int, quality: str?` | `list[Candidate]` |
| `flag_for_training` | `message_id: int, quality: str, tags: list[str]?` | `{success}` |

## Data Model

```sql
CREATE TABLE tuning_revisions (
    id BIGSERIAL PRIMARY KEY,
    original_message_id BIGINT,
    revised_message_id BIGINT,
    improvement_notes TEXT,
    reviewer TEXT,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_tr_original ON tuning_revisions(original_message_id);
```

Uses `message_history.training_candidate` and `message_history.quality_flag` from PRD-04D2.

## Auto-Tagging

```python
def extract_tags(msg: MessageRecord) -> list[str]:
    tags = []
    if msg.agent_name: tags.append(f"agent:{msg.agent_name}")
    if msg.sub_agent_type: tags.append(f"subagent:{msg.sub_agent_type}")
    if "<npl-block" in str(msg.response): tags.append("npl:structured-reflection")
    if msg.repo_url:
        domain = infer_domain(msg.repo_url)  # "infra", "frontend", etc.
        tags.append(f"domain:{domain}")
    return tags
```

## Export Format

**JSONL (OpenAI-compatible)**:
```json
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

**Anthropic format**: Same messages array, different wrapping.

## Key Files

```
npl-context/src/npl_context/
├── tools/tuning.py            # ~300 lines — Dataset tools
├── utils/quality_detector.py  # ~150 lines — Auto-tagging heuristics
├── models/tuning.py           # ~80 lines — TuningExample, Candidate
└── storage/db.py              # +100 lines — Dataset queries
```

## Future Phases

- Automated cleanup (PII removal, code formatting)
- Conversation optimization (remove redundant turns)
- Active learning: identify weak areas, generate targeted examples
- Dataset versioning and comparison
