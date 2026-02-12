# PRD-04B6: Q&A Forum

**Phase**: 5 | **Est**: 2 days | **Repo**: npl-context (FastMCP)

## Context

When agents encounter ambiguities, they can only ask the human operator. This creates a bottleneck. A Q&A forum allows agents to post questions that can be routed to multiple channels (Slack, Jira, web portal) and answered by humans or specialist sub-agents.

## Goals (MVP)

1. Question submission with context and tags
2. Multi-channel routing via webhooks (Slack, Jira)
3. Answer tracking and status management
4. Auto-injection of answers into requesting agent's thread

---

## FastMCP Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `ask_question` | `question: str, context: dict?, tags: list[str]?, channels: list[str]?` | `{question_id}` |
| `answer_question` | `question_id: str, answer: str, answerer: str` | `{success}` |
| `list_questions` | `status: str?, tags: list[str]?, limit: int` | `list[QuestionSummary]` |
| `get_question` | `question_id: str` | `Question` (with answers) |
| `mark_resolved` | `question_id: str` | `{success}` |

## Data Model

```sql
CREATE TABLE npl_questions (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(64),
    question TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    channels TEXT[] DEFAULT '{}',
    status VARCHAR(32) DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
CREATE INDEX idx_q_status ON npl_questions(status);
CREATE INDEX idx_q_tags ON npl_questions USING GIN(tags);

CREATE TABLE npl_answers (
    answer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID REFERENCES npl_questions(question_id),
    answer TEXT NOT NULL,
    answerer VARCHAR(256),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_a_question ON npl_answers(question_id);

CREATE TABLE npl_question_routing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID REFERENCES npl_questions(question_id),
    channel VARCHAR(64) NOT NULL,
    delivery_status VARCHAR(32) DEFAULT 'pending',
    routed_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Hook Integration

**Pre-request hook** (`inject_answers`):
1. Check if session has open questions
2. Query for new answers since last check
3. Inject: `[Answer received for: "{question}"] {answer} — {answerer}`

**Webhook routing** (on question creation):
1. For each channel in `channels`:
   - `slack`: POST to configured webhook URL
   - `jira`: Create issue via Jira API
   - `web`: Store for web portal display

## Configuration

```yaml
# ~/.config/npl-context/channels.yaml
channels:
  slack:
    webhook_url: ${SLACK_WEBHOOK_URL}
    default: true
  jira:
    url: ${JIRA_URL}
    token: ${JIRA_TOKEN}
    project: AGENT
```

## Key Files

```
npl-context/src/npl_context/
├── tools/qna.py               # ~300 lines
├── hooks/pre_request.py       # +100 lines — Answer injection
├── hooks/webhooks.py          # ~150 lines — Channel routing
├── models/qna.py              # ~100 lines
└── storage/db.py              # +100 lines — Q&A queries
```

## Future Phases

- Long-lived specialist sub-agents answering domain questions
- Web portal for Q&A browsing
- Question prioritization and escalation
- Convert high-quality Q&As to KB entries
- NPL chatroom/message inbox integration
