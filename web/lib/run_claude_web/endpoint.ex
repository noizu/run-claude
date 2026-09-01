defmodule RunClaudeWeb.Endpoint do
  use Phoenix.Endpoint, otp_app: :run_claude_web

  # Hologram's client runtime is served from the "hologram" path;
  # our own assets from "assets".
  plug Plug.Static,
    at: "/",
    from: :run_claude_web,
    only: ["assets", "hologram"],
    gzip: false

  plug Plug.Parsers,
    parsers: [:urlencoded, :multipart, :json],
    pass: ["*/*"],
    json_decoder: Jason

  plug Plug.Session,
    store: :cookie,
    key: "_run_claude_web_key",
    signing_salt: "runClaudeWeb"

  # Hologram's router must run BEFORE the Phoenix router.
  plug Hologram.Router
  plug RunClaudeWeb.Router
end
