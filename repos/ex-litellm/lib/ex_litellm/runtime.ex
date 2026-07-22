defmodule ExLiteLLM.Runtime do
  @moduledoc """
  Resolved runtime settings for a single ex-litellm process.

  Mirrors the launch contract of the Python `litellm` binary plus run-claude's
  front proxy: CLI flags (`--host/--port/--config`) layered over environment
  variables (`LITELLM_MASTER_KEY`, `LITELLM_DATABASE_URL`, `STORE_MODEL_IN_DB`)
  layered over compiled defaults.

  Held in `:persistent_term` after boot so any process (plugs, router, front
  proxy) can read it without a GenServer round-trip.
  """

  @pt_key {__MODULE__, :settings}

  @type t :: %__MODULE__{
          host: String.t(),
          litellm_port: non_neg_integer(),
          front_port: non_neg_integer(),
          config_path: String.t() | nil,
          master_key: String.t() | nil,
          database_url: String.t() | nil,
          store_model_in_db: boolean(),
          start_front: boolean()
        }

  defstruct host: "127.0.0.1",
            litellm_port: 4445,
            front_port: 4446,
            config_path: nil,
            master_key: nil,
            database_url: nil,
            store_model_in_db: true,
            start_front: true

  @doc "Store the resolved settings for the lifetime of the node."
  @spec put(t()) :: :ok
  def put(%__MODULE__{} = settings), do: :persistent_term.put(@pt_key, settings)

  @doc "Fetch resolved settings, falling back to compiled app-env defaults."
  @spec get() :: t()
  def get do
    case :persistent_term.get(@pt_key, nil) do
      %__MODULE__{} = settings -> settings
      nil -> from_app_env()
    end
  end

  @doc "Build settings purely from compiled app-env + env vars (used at app boot / in tests)."
  @spec from_app_env() :: t()
  def from_app_env do
    %__MODULE__{
      host: Application.get_env(:ex_litellm, :host, "127.0.0.1"),
      litellm_port: Application.get_env(:ex_litellm, :litellm_port, 4445),
      front_port: Application.get_env(:ex_litellm, :front_port, 4446),
      # CONFIG_FILE_PATH mirrors litellm — lets the app load config at boot even
      # when it auto-starts (releases / `mix run`) before any CLI code runs.
      config_path: env("CONFIG_FILE_PATH"),
      master_key: env("LITELLM_MASTER_KEY"),
      database_url: env("LITELLM_DATABASE_URL"),
      store_model_in_db: truthy(env("STORE_MODEL_IN_DB"), true),
      start_front: Application.get_env(:ex_litellm, :start_front, true)
    }
  end

  @doc """
  Merge parsed CLI options (from `ExLiteLLM.CLI`) over env + defaults.

  `opts` keys: `:host`, `:port` (the litellm tier port), `:front_port`,
  `:config`.
  """
  @spec resolve(keyword()) :: t()
  def resolve(opts) do
    base = from_app_env()

    %__MODULE__{
      base
      | host: opts[:host] || base.host,
        litellm_port: opts[:port] || base.litellm_port,
        front_port: opts[:front_port] || base.front_port,
        config_path: opts[:config] || base.config_path
    }
  end

  defp env(name) do
    case System.get_env(name) do
      nil -> nil
      "" -> nil
      v -> v
    end
  end

  defp truthy(nil, default), do: default
  defp truthy(v, _default), do: String.downcase(v) in ~w(true 1 yes on)
end
