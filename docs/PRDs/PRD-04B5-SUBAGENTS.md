# PRD-04B5: Sub-Agent Tasks

**Phase**: 5 | **Est**: 3 days | **Repo**: npl-context (FastMCP)

## Context

When a controlling agent spawns sub-agents, there's no structured way to define acceptance criteria, required outputs, or modify instructions after launch. Sub-agents operate in isolation. This module provides structured task definitions that can be injected into sub-agent threads and modified in-flight.

## Goals (MVP)

1. Structured task creation with acceptance criteria and required outputs
2. Link TSGs to tasks (what to do when things go wrong)
3. Post-launch instruction modification with auto-injection
4. Task completion tracking

---

## FastMCP Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `create_task` | `title: str, instructions: str, acceptance: list[str], outputs: list[str]?, tsgs: list[str]?` | `{task_id}` |
| `update_task` | `task_id: str, instructions: str?, acceptance: list[str]?` | `{success, update_id}` |
| `get_task` | `task_id: str` | `Task` (full details) |
| `list_tasks` | `status: str?, parent_session: str?` | `list[TaskSummary]` |
| `assign_task` | `task_id: str, subagent_session_id: str` | `{success}` |
| `mark_task_complete` | `task_id: str, outputs: dict` | `{success}` |
| `attach_tsg` | `task_id: str, tsg_id: str` | `{success}` |

## Data Model

```sql
CREATE TABLE npl_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_session_id VARCHAR(64),
    subagent_session_id VARCHAR(64),
    title VARCHAR(256) NOT NULL,
    instructions TEXT NOT NULL,
    acceptance_criteria TEXT[] DEFAULT '{}',
    required_outputs JSONB DEFAULT '{}',
    linked_tsgs TEXT[] DEFAULT '{}',
    status VARCHAR(32) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    completion_outputs JSONB
);
CREATE INDEX idx_tasks_subagent ON npl_tasks(subagent_session_id);
CREATE INDEX idx_tasks_status ON npl_tasks(status);

CREATE TABLE npl_task_updates (
    update_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES npl_tasks(task_id),
    update_type VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    injected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_updates_task ON npl_task_updates(task_id, injected);
```

## Hook Integration

**Pre-request hook** (`inject_task_updates`):

1. Check if session has an assigned task (`subagent_session_id`)
2. On first request, inject full task context:
   ```
   [Task Assignment: {title}]
   Instructions: {instructions}
   Acceptance Criteria:
   - [ ] {criteria_1}
   - [ ] {criteria_2}
   Required Outputs: {outputs}
   Troubleshooting: {linked TSG titles}
   ```
3. On subsequent requests, check for uninjected updates:
   ```
   [Task Update: Instructions Modified]
   {update content}
   ```
4. Mark updates as injected

## Key Files

```
npl-context/src/npl_context/
├── tools/subagent.py          # ~350 lines
├── hooks/pre_request.py       # +150 lines — Task injection
├── models/task.py             # ~150 lines
└── storage/db.py              # +150 lines — Task CRUD
```

## Future Phases

- Interstitial checkpoints (require output X before proceeding to Y)
- Callback triggers (webhook when task reaches state)
- Task DAGs (dependent task workflows)
- Task templates library
- Eval integration (auto-score task output)
