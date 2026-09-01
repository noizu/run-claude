# PRD-04D1: Dynamic Behavior Settings

**Phase**: 6 | **Est**: 2 days | **Repo**: run-claude

## Context

Some models run LoRA soups or exotic setups with runtime-switchable behavior modes (e.g., "wordplay mode", "formal mode", "debug mode"). This adds model metadata about available behaviors and a proxy-level routing mechanism to switch modes via conversation flags or tool calls.

## Goals (MVP)

1. Model metadata field for available behavior alterations
2. Proxy routing: `model-name` + behavior flag → rerouted endpoint
3. CLI command for listing/setting behavior modes
4. State tracking of active behavior per session

---

## Model Metadata Extension

### Modified File: `run_claude/models.yaml`

```yaml
model_list:
  - model_name: some-agent-model
    litellm_params:
      model: openai/gpt-4
      api_base: http://localhost:8000/v1
    behaviors:  # NEW optional field
      wordplay:
        description: "Enhanced creative wordplay"
        route_suffix: "/wordplay"
      formal:
        description: "Strictly formal communication"
        route_suffix: "/formal"
      debug:
        description: "Verbose step-by-step reasoning"
        route_suffix: "/debug"
```

### Modified File: `run_claude/profiles.py`

```python
@dataclass
class BehaviorConfig:
    name: str
    description: str
    route_suffix: str
    parameters: dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelDef:
    model_name: str
    litellm_params: dict[str, Any]
    behaviors: dict[str, BehaviorConfig] = field(default_factory=dict)  # NEW
```

## Routing Mechanism

### New File: `run_claude/callbacks/behavior_router.py`

```python
class BehaviorRouter(CustomLogger):
    """Routes requests to behavior-specific endpoints."""

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        behavior = data.get("metadata", {}).get("behavior_mode")
        if not behavior:
            return data

        model = data.get("model", "")
        behavior_config = self._get_behavior(model, behavior)
        if behavior_config:
            # Append route suffix to api_base
            api_base = data.get("litellm_params", {}).get("api_base", "")
            data["litellm_params"]["api_base"] = api_base + behavior_config["route_suffix"]

        return data
```

## CLI Integration

### Modified File: `run_claude/cli.py`

```bash
run-claude behavior list                # List behaviors for current profile
run-claude behavior list --model X      # List behaviors for specific model
run-claude behavior set wordplay        # Set behavior for current session
run-claude behavior clear               # Reset to default
```

### Modified File: `run_claude/state.py`

```python
@dataclass
class State:
    # ... existing fields ...
    active_behaviors: dict[str, str] = field(default_factory=dict)  # token → behavior
```

## Key Files

| File | Changes |
|------|---------|
| `run_claude/models.yaml` | Add `behaviors` field to model entries |
| `run_claude/profiles.py` | Add `BehaviorConfig` dataclass, extend `ModelDef` |
| `run_claude/callbacks/behavior_router.py` | New: routing callback |
| `run_claude/cli.py` | Add `behavior` subcommand |
| `run_claude/state.py` | Add `active_behaviors` field |

## Future Phases

- Dynamic LoRA loading via adapter API
- Per-message behavior switching
- Behavior composition (combine multiple modes)
- Automatic behavior selection based on task type
- Behavior performance analytics
