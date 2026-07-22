defmodule ExLiteLLM.Deployments do
  @moduledoc """
  Read access over the configured `model_list`.

  A "deployment" is one `model_list` entry: `%{"model_name" => ..,
  "litellm_params" => %{"model" => .., "api_key" => .., "api_base" => ..}}`.
  A client's requested `model` matches a deployment by `model_name`. Multiple
  deployments can share a `model_name` (a load-balanced group) — the router
  picks among them in a later phase; here `lookup/1` returns the first match.

  Later phases add DB-backed deployments (`store_model_in_db`) and runtime
  registration via `/model/new`; this module is the single read surface both the
  YAML and DB sources feed.
  """

  alias ExLiteLLM.Config

  @doc "All deployments matching a requested model_name (a model group)."
  @spec group(String.t()) :: [map()]
  def group(model_name) when is_binary(model_name) do
    Config.get().model_list
    |> Enum.filter(&(&1["model_name"] == model_name))
  end

  @doc "First deployment matching model_name, or nil."
  @spec lookup(String.t()) :: map() | nil
  def lookup(model_name), do: model_name |> group() |> List.first()

  @doc "All configured deployments."
  @spec all() :: [map()]
  def all, do: Config.get().model_list

  @doc "Distinct model_names (for `/v1/models`)."
  @spec model_names() :: [String.t()]
  def model_names do
    all()
    |> Enum.map(& &1["model_name"])
    |> Enum.reject(&is_nil/1)
    |> Enum.uniq()
  end
end
