# PRD-04D2: Task Evals

**Phase**: 5 | **Est**: 2 days | **Repo**: npl-context (FastMCP)

## Context

Sub-agent output quality varies. Currently, control agents must read full output to assess quality. This module parses NPL reflection blocks, scores quality automatically, and conditionally summarizes low-quality output to conserve context.

## Goals (MVP)

1. NPL reflection block parser
2. Emoji-weighted quality scorer (0.0 to 1.0)
3. Conditional summarization: low score → summary, high score → full payload
4. MCP tools for control agents to flag quality for training data
5. Check-in protocol convention for sub-agents

---

## NPL Reflection Parser

```python
EMOJI_WEIGHTS = {
    "✅": +1.0,   # Verified correct
    "🐛": -0.8,   # Bug
    "🔒": -1.0,   # Security vulnerability
    "⚠️": -0.4,   # Pitfall
    "🧩": -0.5,   # Unhandled edge case
    "📝": -0.3,   # TODO/incomplete
    "🚀": +0.5,   # Improvement
    "🔄": -0.2,   # Refactor needed
    "❓": -0.3,   # Needs clarification
}

@dataclass
class ReflectionItem:
    emoji: str
    category: str  # mapped from emoji
    text: str

@dataclass
class ParsedReflection:
    items: list[ReflectionItem]
    score: float  # normalized 0.0-1.0
    categories: dict[str, int]  # count per category
```

**Scoring formula**: `score = (sum_of_weights + abs(min_possible)) / (max_possible + abs(min_possible))`

## FastMCP Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `evaluate_output` | `output: str, acceptance_criteria: list[str]?, threshold: float = 0.6` | `{score, summary?, full_payload?, recommendation}` |
| `request_full_payload` | `task_id: str` | `{full_output}` |
| `flag_sequence_quality` | `task_id: str, quality: str, tags: list[str]?` | `{success}` |

### Recommendation Logic

```
score >= 0.8  → "approve" (return full payload)
0.6 <= score < 0.8  → "review" (return full payload + warnings)
score < 0.6  → "request_revision" (return summary only)
```

## Check-in Convention

Sub-agents should include check-in blocks at key milestones:

```markdown
<npl-block type="check-in" task-id="task-123">
acceptance_criteria:
  - ✅ Implements JWT authentication
  - ✅ Includes unit tests
  - 🐛 Rate limiting has race condition
  - ❓ OAuth scope needs clarification
status: in_progress
next_steps:
  - Fix rate limiting
  - Clarify OAuth with control agent
</npl-block>
```

## Data Model

Extends `message_history` table (from PRD-04C):

```sql
ALTER TABLE message_history ADD COLUMN eval_score FLOAT;
ALTER TABLE message_history ADD COLUMN eval_summary TEXT;
ALTER TABLE message_history ADD COLUMN quality_flag VARCHAR(32);
ALTER TABLE message_history ADD COLUMN training_candidate BOOLEAN DEFAULT FALSE;
```

## Key Files

```
npl-context/src/npl_context/
├── tools/eval.py              # ~250 lines — Eval tools
├── utils/npl_parser.py        # ~200 lines — Reflection + check-in parser
├── models/eval.py             # ~100 lines — EvalResult, ParsedReflection
└── hooks/post_response.py     # +100 lines — Auto-score NPL blocks
```

## Future Phases

- ML-based eval models
- Multi-dimensional scoring (correctness, style, security)
- Automated remediation suggestions
- Real-time eval streaming during sub-agent execution
- Eval dashboard
