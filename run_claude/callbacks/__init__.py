"""
LiteLLM custom callbacks for request/response transformation.

These callbacks allow massaging requests to work with finicky providers
like Groq that have strict input requirements.
"""

from .provider_compat import (
    ProviderCompatCallback,
    standardize_request,
    transform_request_for_provider,
    STRICT_PROVIDERS,
)

__all__ = [
    "ProviderCompatCallback",
    "standardize_request",
    "transform_request_for_provider",
    "STRICT_PROVIDERS",
]
