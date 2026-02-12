# PRD-05: TUI & Terminal Experience

**Phase**: 6 | **Est**: 3 days | **Repo**: run-claude

## Context

Profile and model configuration currently requires manual YAML editing. A Rich-based TUI provides interactive editing, validation, and testing of configurations.

## Goals (MVP)

1. Interactive TUI for editing profiles and model settings
2. Hyperparameter tuning interface
3. Validation suite: test profiles against Claude, Aider, Cursor

---

## TUI Main Menu

```
╭───────────────────────────────────╮
│     run-claude configuration      │
╰───────────────────────────────────╯

  1. Profiles     — View/edit profile configurations
  2. Models       — View/edit model definitions
  3. Hyperparams  — Tune model parameters
  4. Validate     — Test profile connectivity
  5. Status       — Proxy & service status
  q. Quit
```

## Key Screens

### Profile Editor
- List all profiles with tier models in a table
- Select profile → show YAML with syntax highlighting
- Edit individual fields (opus_model, sonnet_model, haiku_model)
- Validate: check model references exist
- Save changes to `~/.config/run-claude/user.profiles.yaml`

### Model Editor
- List models with provider, API base
- Select model → show full litellm_params
- Edit fields interactively
- Save to `~/.config/run-claude/models.yaml`

### Hyperparameter Tuner
```
┌─────────────────────────────────────────┐
│ Model: cerebras-llama-3.3-70b           │
├──────────────┬──────────┬───────────────┤
│ Parameter    │ Current  │ Range         │
├──────────────┼──────────┼───────────────┤
│ temperature  │ 1.0      │ 0.0 - 2.0    │
│ max_tokens   │ 4096     │ 1 - 100000   │
│ top_p        │ 1.0      │ 0.0 - 1.0    │
│ drop_params  │ true     │ true/false    │
└──────────────┴──────────┴───────────────┘
```

### Validation Suite

```python
class ValidationSuite:
    async def validate_profile(self, profile: str) -> ValidationReport:
        # 1. Check proxy running
        # 2. Load profile, resolve models
        # 3. For each model: send test request through proxy
        # 4. Test with Claude Code format
        # 5. Test with Aider format
        # 6. Test with Cursor format
        return report
```

Test request format per tool:
- **Claude Code**: Standard Anthropic API format with model routing
- **Aider**: OpenAI-compatible chat completion
- **Cursor**: OpenAI-compatible with streaming

## CLI Integration

```bash
run-claude tui                    # Launch full TUI
run-claude tui --profile anthropic  # Jump to profile editor
run-claude validate anthropic       # CLI-only validation
run-claude validate --all           # Validate all profiles
```

## Dependencies

Add to `pyproject.toml`:
```toml
dependencies = [
    # ... existing ...
    "rich>=13.0",
]
```

## Key Files

```
run_claude/
├── tui/
│   ├── __init__.py
│   ├── app.py              # ~200 lines — Main TUI loop + menus
│   ├── profile_editor.py   # ~150 lines — Profile editing screen
│   ├── model_editor.py     # ~150 lines — Model editing screen
│   ├── tuner.py            # ~100 lines — Hyperparameter interface
│   └── validation.py       # ~200 lines — Validation suite
├── cli.py                  # Add tui + validate subcommands
```

## Future Phases

- Profile templates (quick start configurations)
- Performance benchmarking during validation
- Cost estimation per profile
- Web-based UI (FastHTML or Gradio)
- Codeplex, Warp, Gemini validation
