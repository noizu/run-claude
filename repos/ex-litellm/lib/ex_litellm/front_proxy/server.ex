defmodule ExLiteLLM.FrontProxy.Server do
  @moduledoc """
  The front-proxy tier (dev :4446 → prod :4443) — a Plug router that replaces
  `run_claude/front_proxy.py`.

  It receives Claude Code's traffic, decides `{target, auth_mode}` via the
  runtime-alterable `RouterLogic`/`Rules`, rewrites headers (hop-by-hop
  stripping + optional master-key swap), and forwards to either the LiteLLM tier
  or the Anthropic API — streaming or buffered depending on the client's
  `Accept`. It also serves:

    * `GET /health` — run-claude's readiness gate for the front tier.
    * `GET /api/claude_cli/bootstrap` — returns available models from the
      LiteLLM tier as `additional_model_options`.
    * `GET/PUT /front/rules`, `PUT /front/mode` — live routing administration
      (master-key gated).

  Bodies are read raw (not JSON-parsed) so arbitrary upstreams are proxied
  faithfully; the routing decision peeks at `model` by decoding the body only
  when needed.
  """
  use Plug.Router

  require Logger

  alias ExLiteLLM.FrontProxy.{Bootstrap, RouterLogic, Rules}
  alias ExLiteLLM.Runtime

  # Headers not forwarded upstream.
  @hop_by_hop ~w(host connection keep-alive transfer-encoding te trailer upgrade content-length)
  # Response headers stripped before returning to the client.
  @strip_resp ~w(content-encoding content-length transfer-encoding)

  plug(:match)
  plug(:dispatch)

  # --- special routes (before the catch-all proxy) ---

  get "/health" do
    send_json(conn, 200, %{status: "ok"})
  end

  get "/api/claude_cli/bootstrap" do
    send_json(conn, 200, Bootstrap.model_options())
  end

  get "/front/rules" do
    gated(conn, fn c -> send_json(c, 200, %{mode: Rules.mode(), rules: encode_rules(Rules.list())}) end)
  end

  put "/front/rules" do
    gated(conn, fn c ->
      {:ok, body, c} = read_full_body(c)

      case decode_rules(body) do
        {:ok, rules} ->
          Rules.put(rules)
          send_json(c, 200, %{status: "ok", count: length(rules)})

        {:error, reason} ->
          send_json(c, 400, %{error: %{message: "invalid rules: #{inspect(reason)}"}})
      end
    end)
  end

  put "/front/mode" do
    gated(conn, fn c ->
      {:ok, body, c} = read_full_body(c)

      with {:ok, %{"mode" => mode_str}} <- Jason.decode(body),
           mode when mode in [:standard, :passthrough] <- to_mode(mode_str),
           :ok <- Rules.set_mode(mode) do
        send_json(c, 200, %{status: "ok", mode: mode})
      else
        _ -> send_json(c, 400, %{error: %{message: "mode must be 'standard' or 'passthrough'"}})
      end
    end)
  end

  # --- the proxy catch-all ---

  match _ do
    forward(conn)
  end

  # === forwarding ===

  defp forward(conn) do
    {:ok, raw_body, conn} = read_full_body(conn)
    decoded = safe_decode(raw_body)

    {target_base, auth_mode} = RouterLogic.route(conn.request_path, decoded)
    url = target_base <> conn.request_path <> qs(conn)
    headers = forward_headers(conn, auth_mode)

    if streaming?(conn) do
      stream_forward(conn, url, headers, raw_body)
    else
      buffered_forward(conn, url, headers, raw_body)
    end
  end

  defp buffered_forward(conn, url, headers, body) do
    case Req.request(
           method: method_atom(conn.method),
           url: url,
           headers: headers,
           body: body,
           decode_body: false,
           retry: false,
           receive_timeout: 600_000
         ) do
      {:ok, %Req.Response{status: status, headers: resp_headers, body: resp_body}} ->
        conn
        |> put_resp_headers(resp_headers)
        |> send_resp(status, resp_body)

      {:error, exc} ->
        proxy_error(conn, exc)
    end
  end

  defp stream_forward(conn, url, headers, body) do
    conn = send_chunked(conn, 200)
    # Seed the per-request conn before Req's into/2 callback fires (each request
    # runs in its own process, so the process dict is a safe carrier).
    conn_ref_put(conn)

    result =
      Req.request(
        method: method_atom(conn.method),
        url: url,
        headers: headers,
        body: body,
        decode_body: false,
        retry: false,
        receive_timeout: 600_000,
        into: fn {:data, data}, {req, resp} ->
          case chunk(conn_ref_get(), data) do
            {:ok, c} -> conn_ref_put(c)
            {:error, _} -> :ok
          end

          {:cont, {req, resp}}
        end
      )

    case result do
      {:ok, _resp} ->
        conn_ref_get()

      {:error, exc} ->
        Logger.error("[front-proxy] stream error: #{inspect(exc)}")
        conn_ref_get()
    end
  end

  # === headers ===

  defp forward_headers(conn, auth_mode) do
    base =
      conn.req_headers
      |> Enum.reject(fn {k, _v} -> String.downcase(k) in @hop_by_hop end)

    case auth_mode do
      :master_key ->
        master = Runtime.get().master_key || ""

        base
        |> reject_header("authorization")
        |> Kernel.++([{"authorization", "Bearer " <> master}])

      :passthrough ->
        base
    end
  end

  defp reject_header(headers, name) do
    Enum.reject(headers, fn {k, _v} -> String.downcase(k) == name end)
  end

  defp put_resp_headers(conn, resp_headers) do
    Enum.reduce(resp_headers, conn, fn {k, v}, acc ->
      if String.downcase(k) in @strip_resp do
        acc
      else
        put_resp_header(acc, String.downcase(k), to_string(v))
      end
    end)
  end

  # === helpers ===

  defp streaming?(conn) do
    case get_req_header(conn, "accept") do
      [accept | _] -> String.contains?(accept, "text/event-stream")
      _ -> false
    end
  end

  defp qs(%{query_string: ""}), do: ""
  defp qs(%{query_string: q}), do: "?" <> q

  defp method_atom(method), do: method |> String.downcase() |> String.to_atom()

  defp safe_decode(""), do: %{}

  defp safe_decode(body) do
    case Jason.decode(body) do
      {:ok, map} when is_map(map) -> map
      _ -> %{}
    end
  end

  defp read_full_body(conn, acc \\ "") do
    case read_body(conn, length: 8_000_000) do
      {:ok, chunk, conn} -> {:ok, acc <> chunk, conn}
      {:more, chunk, conn} -> read_full_body(conn, acc <> chunk)
      {:error, _} = err -> err
    end
  end

  defp proxy_error(conn, exc) do
    Logger.error("[front-proxy] upstream error: #{inspect(exc)}")

    send_json(conn, 502, %{
      type: "error",
      error: %{type: "api_error", message: "front-proxy upstream request failed"}
    })
  end

  defp send_json(conn, status, body) do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(status, Jason.encode!(body))
  end

  # Master-key gate for admin routes.
  defp gated(conn, fun) do
    master = Runtime.get().master_key

    cond do
      is_nil(master) or master == "" -> fun.(conn)
      provided_key(conn) == master -> fun.(conn)
      true -> send_json(conn, 401, %{error: %{message: "unauthorized"}})
    end
  end

  defp provided_key(conn) do
    case get_req_header(conn, "authorization") do
      ["Bearer " <> key | _] -> String.trim(key)
      [key | _] -> String.trim(key)
      _ -> nil
    end
  end

  defp to_mode("standard"), do: :standard
  defp to_mode("passthrough"), do: :passthrough
  defp to_mode(_), do: :invalid

  # Per-request conn carried across Req's into/2 callback via the process dict.
  defp conn_ref_get, do: Process.get(:exll_front_conn)
  defp conn_ref_put(conn), do: (Process.put(:exll_front_conn, conn) && conn)

  # --- rule (de)serialization for the admin API ---

  defp encode_rules(rules) do
    Enum.map(rules, fn %Rules.Rule{match: match, target: target, auth: auth} ->
      %{match: encode_match(match), target: encode_target(target), auth: to_string(auth)}
    end)
  end

  defp encode_match({:path_in, paths}), do: %{type: "path_in", paths: paths}
  defp encode_match({:messages_model, prefix}), do: %{type: "messages_model", prefix: prefix}
  defp encode_match({:messages_not_model, prefix}), do: %{type: "messages_not_model", prefix: prefix}
  defp encode_match(:any), do: %{type: "any"}

  defp encode_target(:litellm), do: %{type: "litellm"}
  defp encode_target(:anthropic), do: %{type: "anthropic"}
  defp encode_target({:url, url}), do: %{type: "url", url: url}

  defp decode_rules(body) do
    with {:ok, %{"rules" => raw}} when is_list(raw) <- Jason.decode(body) do
      {:ok, Enum.map(raw, &decode_rule/1)}
    else
      {:ok, _} -> {:error, :missing_rules_key}
      err -> err
    end
  rescue
    e -> {:error, e}
  end

  defp decode_rule(%{"match" => m, "target" => t, "auth" => a}) do
    %Rules.Rule{match: decode_match(m), target: decode_target(t), auth: String.to_existing_atom(a)}
  end

  defp decode_match(%{"type" => "path_in", "paths" => paths}), do: {:path_in, paths}
  defp decode_match(%{"type" => "messages_model", "prefix" => p}), do: {:messages_model, p}
  defp decode_match(%{"type" => "messages_not_model", "prefix" => p}), do: {:messages_not_model, p}
  defp decode_match(%{"type" => "any"}), do: :any

  defp decode_target(%{"type" => "litellm"}), do: :litellm
  defp decode_target(%{"type" => "anthropic"}), do: :anthropic
  defp decode_target(%{"type" => "url", "url" => url}), do: {:url, url}
end
