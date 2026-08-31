defmodule RunClaudeWeb.Router do
  use Phoenix.Router

  get "/healthz", RunClaudeWeb.Controllers.Health, :show
end
