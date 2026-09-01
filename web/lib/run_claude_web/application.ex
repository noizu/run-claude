defmodule RunClaudeWeb.Application do
  use Application

  @impl true
  def start(_type, _args) do
    children = [
      {Phoenix.PubSub, name: RunClaudeWeb.PubSub},
      RunClaudeWeb.Endpoint
    ]

    opts = [strategy: :one_for_one, name: RunClaudeWeb.Supervisor]
    Supervisor.start_link(children, opts)
  end
end
