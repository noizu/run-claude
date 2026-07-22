defmodule ExLiteLLM.Proxy.Status do
  @moduledoc """
  Human-friendly status page — `GET /status` (HTML) and `GET /status.json`.

  Shows what the gateway is doing right now: version, uptime, listen address,
  routing mode + rules, registered deployments (credentials redacted), active
  cooldowns, and DB state. Master-key gated like the other admin surfaces —
  deployment names/models are configuration, not for anonymous eyes.
  """

  import Plug.Conn

  alias ExLiteLLM.FrontProxy.Rules
  alias ExLiteLLM.Router
  alias ExLiteLLM.Router.CooldownCache
  alias ExLiteLLM.Runtime

  @doc "GET /status.json — machine-readable status."
  def json(conn) do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(200, Jason.encode!(snapshot()))
  end

  @doc "GET /status — HTML status page."
  def html(conn) do
    conn
    |> put_resp_content_type("text/html")
    |> send_resp(200, render(snapshot()))
  end

  # --- data ---

  defp snapshot do
    settings = Runtime.get()
    {wall_ms, _} = :erlang.statistics(:wall_clock)

    %{
      service: "ex-litellm",
      version: ExLiteLLM.version(),
      listen: "#{settings.host}:#{settings.port}",
      uptime_seconds: div(wall_ms, 1000),
      config_path: settings.config_path,
      db: db_info(settings),
      front_proxy: %{
        mode: Rules.mode(),
        rules: length(Rules.list())
      },
      deployments: deployments(),
      cooldowns: CooldownCache.active()
    }
  end

  defp deployments do
    Enum.map(Router.deployments(), fn d ->
      %{
        model_name: d["model_name"],
        model: get_in(d, ["litellm_params", "model"]),
        api_base: get_in(d, ["litellm_params", "api_base"]),
        model_id: d["model_id"]
      }
    end)
  end

  defp db_info(settings) do
    %{
      backend: if(settings.database_url, do: redact(settings.database_url), else: "sqlite (default)"),
      connected: Process.whereis(ExLiteLLM.Schema.Repo) != nil
    }
  end

  defp redact(url), do: Regex.replace(~r{://([^:/@]+):([^@]+)@}, url, "://\\1:****@")

  # --- render ---

  defp render(s) do
    """
    <!doctype html>
    <html><head><meta charset="utf-8"><title>ex-litellm status</title>
    <meta http-equiv="refresh" content="10">
    <style>
      :root { color-scheme: light dark; }
      body { font: 14px/1.5 -apple-system, "Segoe UI", sans-serif; max-width: 900px;
             margin: 2rem auto; padding: 0 1rem; }
      h1 { font-size: 1.3rem; } h2 { font-size: 1.05rem; margin-top: 1.6rem; }
      .ok { color: #2e9e44; font-weight: 600; }
      table { border-collapse: collapse; width: 100%; }
      th, td { text-align: left; padding: .35rem .6rem; border-bottom: 1px solid #8884; }
      th { font-weight: 600; }
      code { background: #8882; padding: .1rem .3rem; border-radius: 3px; }
      .meta td:first-child { font-weight: 600; width: 11rem; }
      .empty { opacity: .6; font-style: italic; }
    </style></head><body>
    <h1>ex-litellm <span class="ok">&#9679; running</span></h1>
    <table class="meta">
      <tr><td>Version</td><td>#{h(s.version)}</td></tr>
      <tr><td>Listen</td><td><code>#{h(s.listen)}</code></td></tr>
      <tr><td>Uptime</td><td>#{uptime(s.uptime_seconds)}</td></tr>
      <tr><td>Config</td><td><code>#{h(s.config_path || "(none)")}</code></td></tr>
      <tr><td>Database</td><td><code>#{h(s.db.backend)}</code> — #{if s.db.connected, do: ~s(<span class="ok">connected</span>), else: "down"}</td></tr>
      <tr><td>Routing mode</td><td><code>#{h(s.front_proxy.mode)}</code> (#{s.front_proxy.rules} rules — <a href="/front/rules">view</a>)</td></tr>
    </table>

    <h2>Deployments (#{length(s.deployments)})</h2>
    #{deployments_table(s.deployments)}

    <h2>Active cooldowns (#{length(s.cooldowns)})</h2>
    #{cooldowns_list(s.cooldowns)}

    <p style="margin-top:2rem;opacity:.6">auto-refreshes every 10s ·
      <a href="/status.json">status.json</a> · <a href="/health">health</a> ·
      <a href="/model/info">model/info</a></p>
    </body></html>
    """
  end

  defp deployments_table([]), do: ~s(<p class="empty">none registered</p>)

  defp deployments_table(deps) do
    rows =
      Enum.map_join(deps, "\n", fn d ->
        "<tr><td><code>#{h(d.model_name)}</code></td><td>#{h(d.model)}</td>" <>
          "<td>#{h(d.api_base || "provider default")}</td><td><code>#{h(short(d.model_id))}</code></td></tr>"
      end)

    """
    <table><tr><th>model_name</th><th>upstream model</th><th>api_base</th><th>id</th></tr>
    #{rows}</table>
    """
  end

  defp cooldowns_list([]), do: ~s(<p class="empty">none — all deployments healthy</p>)

  defp cooldowns_list(ids) do
    "<ul>" <> Enum.map_join(ids, "", &"<li><code>#{h(&1)}</code></li>") <> "</ul>"
  end

  defp uptime(secs) when secs < 60, do: "#{secs}s"
  defp uptime(secs) when secs < 3600, do: "#{div(secs, 60)}m #{rem(secs, 60)}s"

  defp uptime(secs) do
    h = div(secs, 3600)
    m = div(rem(secs, 3600), 60)
    if h >= 24, do: "#{div(h, 24)}d #{rem(h, 24)}h #{m}m", else: "#{h}h #{m}m"
  end

  defp short(nil), do: "-"
  defp short(id) when byte_size(id) > 10, do: binary_part(id, 0, 10) <> "…"
  defp short(id), do: id

  # Minimal HTML escaping for interpolated values.
  defp h(nil), do: ""

  defp h(value) do
    value
    |> to_string()
    |> String.replace("&", "&amp;")
    |> String.replace("<", "&lt;")
    |> String.replace(">", "&gt;")
  end
end
