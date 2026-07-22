defmodule ExLiteLLM.Deployments do
  @moduledoc """
  Read access over the live deployment set.

  A "deployment" is one `model_list` entry: `%{"model_name" => ..,
  "litellm_params" => %{"model" => .., "api_key" => .., "api_base" => ..}}`.
  A client's requested `model` matches a deployment by `model_name`.

  Deployments are owned by `ExLiteLLM.Router` (seeded from `config.yaml`, mutated
  at runtime by `/model/new|update|delete`). This module is the stable read
  surface for the inference path; it falls back to the static config when the
  Router isn't running (e.g. unit tests that don't start the app).
  """

  alias ExLiteLLM.Config
  alias ExLiteLLM.Router

  @doc "All deployments matching a requested model_name (a model group)."
  @spec group(String.t()) :: [map()]
  def group(model_name) when is_binary(model_name) do
    if router_up?() do
      Router.group(model_name)
    else
      Enum.filter(Config.get().model_list, &(&1["model_name"] == model_name))
    end
  end

  @doc """
  Select a single deployment for a requested model_name (router strategy +
  cooldown filtering when the Router is up; first match otherwise).
  """
  @spec lookup(String.t()) :: map() | nil
  def lookup(model_name) do
    if router_up?() do
      case Router.select(model_name) do
        {:ok, deployment} -> deployment
        {:error, _} -> nil
      end
    else
      model_name |> group() |> List.first()
    end
  end

  @doc "All configured deployments."
  @spec all() :: [map()]
  def all do
    if router_up?(), do: Router.deployments(), else: Config.get().model_list
  end

  @doc "Distinct model_names (for `/v1/models`)."
  @spec model_names() :: [String.t()]
  def model_names do
    all()
    |> Enum.map(& &1["model_name"])
    |> Enum.reject(&is_nil/1)
    |> Enum.uniq()
  end

  defp router_up?, do: Process.whereis(ExLiteLLM.Router) != nil
end
