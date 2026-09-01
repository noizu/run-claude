defmodule RunClaudeWeb.Controllers.Health do
  @moduledoc "Trivial liveness/readiness endpoint for k8s probes."

  use Phoenix.Controller, formats: [html: RunClaudeWeb.ErrorHTML]

  def show(conn, _params), do: send_resp(conn, 200, "ok")
end
