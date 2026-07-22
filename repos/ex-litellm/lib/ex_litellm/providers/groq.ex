defmodule ExLiteLLM.Providers.Groq do
  @moduledoc """
  Groq — OpenAI-compatible. Groq is a "strict" provider: it rejects several
  OpenAI params (e.g. `logit_bias`, `logprobs`, `top_logprobs`, `n>1`), which is
  exactly what run-claude's `provider_compat` callback strips. We narrow the
  supported-param set so `drop_params` removes them before the call.
  """
  use ExLiteLLM.Providers.OpenAICompatible,
    base_url: "https://api.groq.com/openai/v1",
    api_key_env: "GROQ_API_KEY"

  alias ExLiteLLM.Providers.OpenAICompatible.Shared

  # Params Groq does NOT accept — removed from the allowlist.
  @unsupported ~w(logit_bias logprobs top_logprobs)

  @impl true
  def get_supported_openai_params(_model) do
    Shared.default_supported_params() -- @unsupported
  end
end
