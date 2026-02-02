"""
Provider compatibility callback for LiteLLM proxy.

Handles request transformations for providers with strict input requirements
(e.g., Groq, Cerebras) that don't accept certain fields in the request.
"""

from __future__ import annotations

import copy
import sys
from typing import Any, Optional

try:
    from litellm.integrations.custom_logger import CustomLogger
    from litellm.proxy._types import UserAPIKeyAuth
except ImportError:
    # Fallback for when litellm isn't installed (e.g., during package build)
    CustomLogger = object
    UserAPIKeyAuth = Any


# Providers that need special handling
STRICT_PROVIDERS = {
    "groq",
    "cerebras",
    "together",
    "anyscale",
}

# Fields to strip from tool_use blocks for strict providers
TOOL_USE_STRIP_FIELDS = {
    "provider_specific_fields",
    "cache_control",  # Some providers don't support cache hints
}

# Fields to strip from message content blocks
CONTENT_STRIP_FIELDS = {
    "cache_control",
}


def _get_provider_from_model(model: str) -> str | None:
    """Extract provider name from model string (e.g., 'groq/llama3-8b' -> 'groq')."""
    if "/" in model:
        return model.split("/")[0].lower()
    return None


def _strip_fields_from_content(content: Any, fields_to_strip: set[str]) -> Any:
    """
    Recursively strip specified fields from message content.

    Args:
        content: Message content (string, list, or dict)
        fields_to_strip: Set of field names to remove

    Returns:
        Cleaned content with fields stripped
    """
    if isinstance(content, dict):
        # Remove specified fields from this dict
        cleaned = {k: v for k, v in content.items() if k not in fields_to_strip}
        # Recursively clean nested values
        for key, value in cleaned.items():
            cleaned[key] = _strip_fields_from_content(value, fields_to_strip)
        return cleaned
    elif isinstance(content, list):
        return [_strip_fields_from_content(item, fields_to_strip) for item in content]
    else:
        return content


def _clean_tool_use_blocks(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Remove problematic fields from tool_use blocks in messages.

    Some providers (like Groq) return 400 errors when receiving fields
    like 'provider_specific_fields' in tool_use content blocks.
    """
    cleaned_messages = []

    for msg in messages:
        msg_copy = msg.copy()
        content = msg_copy.get("content")

        if isinstance(content, list):
            cleaned_content = []
            for block in content:
                if isinstance(block, dict):
                    block_type = block.get("type", "")

                    if block_type == "tool_use":
                        # Strip problematic fields from tool_use blocks
                        cleaned_block = {
                            k: v for k, v in block.items()
                            if k not in TOOL_USE_STRIP_FIELDS
                        }
                        cleaned_content.append(cleaned_block)
                    elif block_type in ("text", "image", "image_url"):
                        # Strip cache_control and similar from content blocks
                        cleaned_block = {
                            k: v for k, v in block.items()
                            if k not in CONTENT_STRIP_FIELDS
                        }
                        cleaned_content.append(cleaned_block)
                    else:
                        cleaned_content.append(block)
                else:
                    cleaned_content.append(block)
            msg_copy["content"] = cleaned_content
        elif isinstance(content, dict):
            # Single content block as dict
            msg_copy["content"] = _strip_fields_from_content(content, TOOL_USE_STRIP_FIELDS | CONTENT_STRIP_FIELDS)

        cleaned_messages.append(msg_copy)

    return cleaned_messages


def _clean_tools_definition(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
    """
    Clean tool definitions for strict providers.

    Some providers don't accept certain fields in tool schemas.
    """
    if not tools:
        return tools

    cleaned_tools = []
    for tool in tools:
        tool_copy = copy.deepcopy(tool)

        # Remove cache_control from tool definitions if present
        if "cache_control" in tool_copy:
            del tool_copy["cache_control"]

        # Clean function parameters if present
        if "function" in tool_copy and isinstance(tool_copy["function"], dict):
            func = tool_copy["function"]
            if "cache_control" in func:
                del func["cache_control"]

        cleaned_tools.append(tool_copy)

    return cleaned_tools


def transform_request_for_provider(
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    **kwargs: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]] | None, dict[str, Any]]:
    """
    Transform request data for provider compatibility.

    Args:
        model: Model identifier (e.g., 'groq/llama3-8b-8192')
        messages: Request messages
        tools: Tool definitions (optional)
        **kwargs: Additional request parameters

    Returns:
        Tuple of (cleaned_messages, cleaned_tools, cleaned_kwargs)
    """
    provider = _get_provider_from_model(model)

    # Only transform for strict providers
    if provider not in STRICT_PROVIDERS:
        return messages, tools, kwargs

    # Clean messages
    cleaned_messages = _clean_tool_use_blocks(messages)

    # Clean tools
    cleaned_tools = _clean_tools_definition(tools)

    # Clean kwargs - remove any provider-specific fields at top level
    cleaned_kwargs = {
        k: v for k, v in kwargs.items()
        if k not in {"provider_specific_fields", "cache_control"}
    }

    return cleaned_messages, cleaned_tools, cleaned_kwargs


class ProviderCompatCallback(CustomLogger):
    """
    LiteLLM custom callback for provider compatibility transformations.

    This callback intercepts requests before they're sent to providers
    and cleans up fields that cause errors with strict providers like Groq.

    Usage in litellm config.yaml:
        litellm_settings:
          callbacks:
            - run_claude.callbacks.ProviderCompatCallback
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs) if hasattr(super(), '__init__') else None
        self.debug = kwargs.get("debug", False)

    async def async_pre_call_hook(
        self,
        user_api_key_dict: UserAPIKeyAuth,
        cache: Any,
        data: dict[str, Any],
        call_type: str,
    ) -> dict[str, Any]:
        """
        Transform request data before sending to provider.

        This is called by LiteLLM proxy before making the API call.
        """
        model = data.get("model", "")
        provider = _get_provider_from_model(model)

        # Only transform for strict providers
        if provider not in STRICT_PROVIDERS:
            return data

        if self.debug:
            print(f"[ProviderCompatCallback] Transforming request for {provider}", file=sys.stderr)

        # Transform messages
        if "messages" in data:
            data["messages"] = _clean_tool_use_blocks(data["messages"])

        # Transform tools
        if "tools" in data:
            data["tools"] = _clean_tools_definition(data["tools"])

        # Remove top-level problematic fields
        for field in ["provider_specific_fields", "cache_control"]:
            data.pop(field, None)

        return data

    def log_pre_api_call(
        self,
        model: str,
        messages: list[dict[str, Any]],
        kwargs: dict[str, Any],
    ) -> None:
        """
        Called before API call - can be used for logging/debugging.

        Note: This is called after async_pre_call_hook, so transformations
        should already be applied.
        """
        if self.debug:
            provider = _get_provider_from_model(model)
            if provider in STRICT_PROVIDERS:
                print(f"[ProviderCompatCallback] Pre-API call to {model}", file=sys.stderr)

    def log_success_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        """Called on successful API response."""
        pass

    def log_failure_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        """Called on failed API response."""
        if self.debug:
            model = kwargs.get("model", "")
            provider = _get_provider_from_model(model)
            if provider in STRICT_PROVIDERS:
                print(f"[ProviderCompatCallback] API call failed for {model}", file=sys.stderr)


# Standalone function for use as proxy hook (alternative to callback class)
def standardize_request(litellm_params: dict[str, Any]) -> dict[str, Any]:
    """
    Proxy hook function to standardize requests for strict providers.

    Usage in litellm config.yaml:
        general_settings:
          proxy_hooks:
            - run_claude.callbacks.provider_compat.standardize_request
    """
    kwargs = litellm_params.get("kwargs", {})
    model = kwargs.get("model", "")

    provider = _get_provider_from_model(model)
    if provider not in STRICT_PROVIDERS:
        return litellm_params

    # Transform messages
    if "messages" in kwargs:
        kwargs["messages"] = _clean_tool_use_blocks(kwargs["messages"])

    # Transform tools
    if "tools" in kwargs:
        kwargs["tools"] = _clean_tools_definition(kwargs["tools"])

    # Remove problematic top-level fields
    for field in ["provider_specific_fields", "cache_control"]:
        kwargs.pop(field, None)

    litellm_params["kwargs"] = kwargs
    return litellm_params
