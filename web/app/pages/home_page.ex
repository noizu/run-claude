defmodule RunClaudeWeb.Pages.HomePage do
  @moduledoc """
  run-claude landing page — single static route "/" per web/COPY.md.
  No client state or actions needed; SSR only, minimal JS (Hologram runtime).
  """

  use Hologram.Page

  route "/"
  layout RunClaudeWeb.MainLayout

  def init(_params, component, _server) do
    component
  end
end
