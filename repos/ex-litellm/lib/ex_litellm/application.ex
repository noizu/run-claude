defmodule ExLiteLLM.Application do
  @moduledoc """
  ex-litellm OTP application.

  Supervision tree (Phase 1):

    * `ExLiteLLM.Schema.Repo` — Ecto repo (SQLite default)
    * Bandit listener for the **LiteLLM tier** (`ExLiteLLM.Proxy.Endpoint`)

  The front tier, provider registry, model/router GenServers, cooldown ETS, and
  callback manager are added to this tree in their respective phases. HTTP
  listeners are skipped when `:start_servers` is false (unit tests) so the app
  can boot without binding ports.
  """

  use Application

  require Logger

  @impl true
  def start(_type, _args) do
    settings = ExLiteLLM.Runtime.get()

    children =
      [
        repo_child(settings)
      ] ++ server_children(settings)

    opts = [strategy: :one_for_one, name: ExLiteLLM.Supervisor]

    with {:ok, pid} <- Supervisor.start_link(List.flatten(children), opts) do
      log_boot(settings)
      {:ok, pid}
    end
  end

  # --- children ---

  defp repo_child(settings) do
    # Point the repo at the resolved DB path/URL before it starts.
    ExLiteLLM.Schema.Repo.Config.apply(settings)
    ExLiteLLM.Schema.Repo
  end

  defp server_children(settings) do
    if start_servers?() do
      [litellm_listener(settings)]
    else
      []
    end
  end

  defp litellm_listener(settings) do
    {Bandit,
     plug: ExLiteLLM.Proxy.Endpoint,
     scheme: :http,
     ip: parse_ip(settings.host),
     port: settings.litellm_port}
    |> Supervisor.child_spec(id: :litellm_listener)
  end

  # --- helpers ---

  defp start_servers?, do: Application.get_env(:ex_litellm, :start_servers, true)

  defp parse_ip(host) do
    case host |> to_charlist() |> :inet.parse_address() do
      {:ok, ip} -> ip
      {:error, _} -> {127, 0, 0, 1}
    end
  end

  defp log_boot(settings) do
    if start_servers?() do
      Logger.info(
        "[ex-litellm] LiteLLM tier listening on #{settings.host}:#{settings.litellm_port}",
        tier: :litellm
      )
    end
  end
end
