# PRD-03: Lifecycle Hooks

**Phase**: 2 | **Est**: 2 days | **Repo**: run-claude

## Context

The proxy needs an extensible event system for request/response interception. Currently, `provider_compat.py` callback handles provider-specific field stripping but has no general hook infrastructure. Items 4a-4c all require pre-request and post-response hooks.

## Goals

1. Simple event model (like Express middleware or onClick handlers)
2. Hook chain with error isolation (one hook failure doesn't break the chain)
3. YAML-based hook configuration
4. Integration with LiteLLM's CustomLogger callback system
5. Built-in hooks for logging and provider compat

---

## 3a: Event Model

### New File: `run_claude/hooks/__init__.py`

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

class HookEvent(Enum):
    PRE_REQUEST = "pre_request"       # Before sending to provider
    POST_RESPONSE = "post_response"   # After receiving response
    PRE_TOOL_CALL = "pre_tool_call"   # Before tool execution
    POST_TOOL_CALL = "post_tool_call" # After tool execution

@dataclass
class HookContext:
    """Immutable-ish context passed through hook chain."""
    event: HookEvent
    model: str
    provider: str | None
    request_id: str
    timestamp: float
    messages: list[dict] | None = None
    tools: list[dict] | None = None
    response: dict | None = None
    metadata: dict = field(default_factory=dict)
    # Hooks can set this to stop the chain
    stop_chain: bool = False

# Type alias for hook functions
HookFn = Callable[[HookContext], Awaitable[HookContext]]
```

---

## 3b: Hook Chain

### New File: `run_claude/hooks/chain.py`

```python
import logging
from .  import HookEvent, HookContext, HookFn

logger = logging.getLogger("run-claude.hooks")

class HookChain:
    """Execute hooks sequentially with error isolation."""

    def __init__(self):
        self._hooks: dict[HookEvent, list[tuple[str, HookFn]]] = {
            e: [] for e in HookEvent
        }

    def register(self, event: HookEvent, name: str, hook: HookFn) -> None:
        self._hooks[event].append((name, hook))
        logger.debug(f"Registered hook: {name} for {event.value}")

    async def execute(self, ctx: HookContext) -> HookContext:
        for name, hook in self._hooks[ctx.event]:
            if ctx.stop_chain:
                logger.debug(f"Chain stopped before {name}")
                break
            try:
                ctx = await hook(ctx)
            except Exception as e:
                logger.error(f"Hook {name} failed: {e}", exc_info=True)
                # Continue chain — one hook failure doesn't break others
        return ctx

    def list_hooks(self, event: HookEvent | None = None) -> list[str]:
        if event:
            return [name for name, _ in self._hooks[event]]
        return [f"{e.value}:{name}" for e in HookEvent for name, _ in self._hooks[e]]

# Singleton
_chain = HookChain()

def get_hook_chain() -> HookChain:
    return _chain
```

---

## 3c: Hook Configuration

### New Template: `run_claude/hooks.yaml` (installed to `~/.config/run-claude/hooks.yaml`)

```yaml
# Hook configuration for run-claude proxy
# Hooks execute in order listed. Errors are logged but don't stop the chain.

hooks:
  pre_request:
    - name: provider_compat
      module: run_claude.hooks.builtin
      function: strip_provider_fields
      enabled: true

    - name: log_request
      module: run_claude.hooks.builtin
      function: log_request
      enabled: false  # Enable for debugging
      config:
        verbose: false

  post_response:
    - name: log_response
      module: run_claude.hooks.builtin
      function: log_response
      enabled: false
      config:
        include_tokens: true

# Additional Python paths for custom hooks
python_path: []
  # - "${HOME}/my-custom-hooks"
```

### New File: `run_claude/hooks/loader.py`

```python
import importlib
import asyncio
from pathlib import Path
from . import HookEvent, HookFn
from .chain import get_hook_chain

def load_hooks_from_config(config_path: Path) -> int:
    """Load hooks from YAML config. Returns count of hooks registered."""
    config = yaml.safe_load(config_path.read_text())
    count = 0

    # Add custom python paths
    for p in config.get("python_path", []):
        expanded = os.path.expandvars(p)
        if expanded not in sys.path:
            sys.path.insert(0, expanded)

    chain = get_hook_chain()

    for event_name, hook_list in config.get("hooks", {}).items():
        event = HookEvent(event_name)
        for hook_def in hook_list:
            if not hook_def.get("enabled", True):
                continue

            module = importlib.import_module(hook_def["module"])
            fn = getattr(module, hook_def["function"])

            # Wrap sync functions as async
            if not asyncio.iscoroutinefunction(fn):
                sync_fn = fn
                async def async_wrapper(ctx, _fn=sync_fn):
                    return _fn(ctx)
                fn = async_wrapper

            # If hook has config, wrap to inject it
            hook_config = hook_def.get("config", {})
            if hook_config:
                original_fn = fn
                async def configured_wrapper(ctx, _fn=original_fn, _cfg=hook_config):
                    ctx.metadata["hook_config"] = _cfg
                    return await _fn(ctx)
                fn = configured_wrapper

            chain.register(event, hook_def["name"], fn)
            count += 1

    return count
```

---

## 3d: Integration with LiteLLM Callbacks

### Modified File: `run_claude/callbacks/provider_compat.py`

```python
import time
import uuid
from run_claude.hooks import HookEvent, HookContext
from run_claude.hooks.chain import get_hook_chain
from run_claude.hooks.loader import load_hooks_from_config

class ProviderCompatCallback(CustomLogger):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load hooks on callback init (runs inside litellm process)
        hooks_config = Path.home() / ".config" / "run-claude" / "hooks.yaml"
        if hooks_config.exists():
            count = load_hooks_from_config(hooks_config)
            print(f"[HOOKS] Loaded {count} hooks from {hooks_config}")

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        model = data.get("model", "unknown")
        provider = model.split("/")[0] if "/" in model else None

        ctx = HookContext(
            event=HookEvent.PRE_REQUEST,
            model=model,
            provider=provider,
            request_id=str(uuid.uuid4()),
            timestamp=time.time(),
            messages=data.get("messages"),
            tools=data.get("tools"),
            metadata=data.get("metadata", {}),
        )

        chain = get_hook_chain()
        ctx = await chain.execute(ctx)

        # Apply hook modifications back to data
        if ctx.messages is not None:
            data["messages"] = ctx.messages
        if ctx.tools is not None:
            data["tools"] = ctx.tools

        return data

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        model = kwargs.get("model", "unknown")
        provider = model.split("/")[0] if "/" in model else None

        ctx = HookContext(
            event=HookEvent.POST_RESPONSE,
            model=model,
            provider=provider,
            request_id=kwargs.get("litellm_call_id", ""),
            timestamp=time.time(),
            response=response_obj if isinstance(response_obj, dict) else None,
            metadata=kwargs.get("metadata", {}),
        )

        await get_hook_chain().execute(ctx)
```

---

## 3e: Built-in Hooks

### New File: `run_claude/hooks/builtin.py`

```python
"""Built-in hooks for logging and provider compatibility."""

from . import HookContext

async def log_request(ctx: HookContext) -> HookContext:
    """Log outgoing request summary."""
    msg_count = len(ctx.messages) if ctx.messages else 0
    verbose = ctx.metadata.get("hook_config", {}).get("verbose", False)
    print(f"[REQ] {ctx.model} | {msg_count} messages | id={ctx.request_id[:8]}")
    if verbose and ctx.messages:
        last = ctx.messages[-1]
        content = str(last.get("content", ""))[:100]
        print(f"  Last message ({last.get('role')}): {content}...")
    return ctx

async def log_response(ctx: HookContext) -> HookContext:
    """Log incoming response summary."""
    include_tokens = ctx.metadata.get("hook_config", {}).get("include_tokens", True)
    if ctx.response and include_tokens:
        usage = ctx.response.get("usage", {}) if isinstance(ctx.response, dict) else {}
        print(f"[RESP] {ctx.model} | tokens: {usage.get('total_tokens', '?')}")
    else:
        print(f"[RESP] {ctx.model}")
    return ctx

async def strip_provider_fields(ctx: HookContext) -> HookContext:
    """Strip fields that cause errors with strict providers (Groq, Cerebras, etc).

    Replaces the inline logic from the old provider_compat callback.
    """
    STRICT_PROVIDERS = {"groq", "cerebras", "together", "anyscale"}

    if ctx.provider not in STRICT_PROVIDERS:
        return ctx

    if ctx.messages:
        for msg in ctx.messages:
            _clean_message(msg)

    if ctx.tools:
        for tool in ctx.tools:
            tool.pop("cache_control", None)
            if "function" in tool:
                tool["function"].pop("cache_control", None)

    return ctx

def _clean_message(msg: dict) -> None:
    """Remove provider_specific_fields and cache_control from message."""
    msg.pop("provider_specific_fields", None)
    content = msg.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                block.pop("cache_control", None)
                block.pop("provider_specific_fields", None)
```

---

## Testing

### Unit Tests

```python
class TestHookChain:
    @pytest.mark.asyncio
    async def test_execute_runs_all_hooks(self):
        chain = HookChain()
        results = []
        async def hook_a(ctx):
            results.append("a")
            return ctx
        async def hook_b(ctx):
            results.append("b")
            return ctx
        chain.register(HookEvent.PRE_REQUEST, "a", hook_a)
        chain.register(HookEvent.PRE_REQUEST, "b", hook_b)
        ctx = HookContext(event=HookEvent.PRE_REQUEST, model="test", ...)
        await chain.execute(ctx)
        assert results == ["a", "b"]

    @pytest.mark.asyncio
    async def test_error_isolation(self):
        chain = HookChain()
        async def bad_hook(ctx):
            raise ValueError("boom")
        async def good_hook(ctx):
            ctx.metadata["reached"] = True
            return ctx
        chain.register(HookEvent.PRE_REQUEST, "bad", bad_hook)
        chain.register(HookEvent.PRE_REQUEST, "good", good_hook)
        ctx = HookContext(event=HookEvent.PRE_REQUEST, model="test", ...)
        ctx = await chain.execute(ctx)
        assert ctx.metadata["reached"] is True

class TestBuiltinHooks:
    @pytest.mark.asyncio
    async def test_strip_provider_fields_strict(self):
        ctx = HookContext(
            event=HookEvent.PRE_REQUEST,
            model="groq/llama3",
            provider="groq",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "hi", "cache_control": {"type": "ephemeral"}}
            ]}],
            ...
        )
        ctx = await strip_provider_fields(ctx)
        assert "cache_control" not in ctx.messages[0]["content"][0]

    @pytest.mark.asyncio
    async def test_strip_provider_fields_non_strict_passthrough(self):
        ctx = HookContext(
            model="anthropic/claude", provider="anthropic",
            messages=[{"content": [{"cache_control": {"type": "ephemeral"}}]}],
            ...
        )
        ctx = await strip_provider_fields(ctx)
        assert "cache_control" in ctx.messages[0]["content"][0]
```

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Hook performance overhead | Hooks are optional; benchmark; profile slow hooks |
| Async/sync hook mixing | Loader auto-wraps sync functions |
| Hook config YAML errors | Validate on load, skip malformed entries, log warnings |
| Import errors in custom hooks | Catch ImportError per hook, log, continue |
| Hook modifies data destructively | Document: hooks should return modified ctx, not mutate in place |
