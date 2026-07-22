defmodule ExLiteLLM do
  @moduledoc """
  ex-litellm — an interface-identical Elixir reimplementation of the LiteLLM
  proxy, plus run-claude's front-proxy routing tier folded into one app.

  Two HTTP tiers:

    * **LiteLLM tier** (`ExLiteLLM.Proxy.Endpoint`, dev :4445 → prod :4444) —
      the OpenAI-compatible multi-provider inference + admin surface.
    * **Front tier** (`ExLiteLLM.FrontProxy`, dev :4446 → prod :4443) — a
      runtime-alterable routing/auth-swap layer that sits in front of the
      LiteLLM tier and Anthropic passthrough.

  SQLite by default (a single file), Postgres optional. Launched via the
  `ex-litellm` escript (`ExLiteLLM.CLI`) with the same `--host/--port/--config`
  contract as the Python `litellm` binary.
  """

  @version Mix.Project.config()[:version]

  @doc "The ex-litellm version string (reported by health/readiness)."
  @spec version() :: String.t()
  def version, do: @version
end
