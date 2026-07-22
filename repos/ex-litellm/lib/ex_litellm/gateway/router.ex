defmodule ExLiteLLM.Gateway.Router do
  @moduledoc """
  Dispatch logic for the unified gateway's non-native routes — the front-proxy
  routing folded in.

  * `messages/1` — `/v1/messages`. A `claude-*` model is reverse-proxied to
    Anthropic (auth preserved); a non-`claude-*` model is served by the native
    inference path (translated OpenAI ↔ provider), because ex-litellm speaks
    those providers itself now.
  * `passthrough/1` — any other path. Resolved against the runtime rule table;
    typically an Anthropic passthrough.
  * `get_rules/1` / `put_rules/1` / `put_mode/1` — live rule administration.
  """

  import Plug.Conn

  alias ExLiteLLM.FrontProxy.{Rules, RouterLogic}
  alias ExLiteLLM.Gateway.Forwarder
  alias ExLiteLLM.Proxy.Inference

  @anthropic "https://api.anthropic.com"

  @doc "Handle POST /v1/messages."
  def messages(conn) do
    body = conn.assigns[:json_body] || %{}
    model = RouterLogic.extract_model(body)

    if String.starts_with?(model, "claude-") do
      # Native Anthropic shape → forward upstream, preserve caller auth.
      Forwarder.forward(conn, @anthropic, :passthrough, raw_body())
    else
      # Non-claude model on the messages endpoint → serve via native inference.
      # (litellm proxies these to the target provider; we do too.)
      Inference.chat_completions(conn)
    end
  end

  @doc "Handle any non-native path via the runtime rule table."
  def passthrough(conn) do
    body = conn.assigns[:json_body] || %{}
    {target_base, auth_mode} = RouterLogic.route(conn.request_path, body)
    Forwarder.forward(conn, target_base, auth_mode, raw_body())
  end

  # --- admin ---

  def get_rules(conn) do
    json(conn, 200, %{mode: Rules.mode(), rules: encode_rules(Rules.list())})
  end

  def put_rules(conn) do
    case decode_rules(conn.assigns[:json_body]) do
      {:ok, rules} ->
        Rules.put(rules)
        json(conn, 200, %{status: "ok", count: length(rules)})

      {:error, reason} ->
        json(conn, 400, %{error: %{message: "invalid rules: #{inspect(reason)}"}})
    end
  end

  def put_mode(conn) do
    with %{"mode" => mode_str} <- conn.assigns[:json_body],
         mode when mode in [:standard, :passthrough] <- to_mode(mode_str),
         :ok <- Rules.set_mode(mode) do
      json(conn, 200, %{status: "ok", mode: mode})
    else
      _ -> json(conn, 400, %{error: %{message: "mode must be 'standard' or 'passthrough'"}})
    end
  end

  # --- helpers ---

  defp raw_body, do: Process.get(:exll_raw_body, "")

  defp json(conn, status, body) do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(status, Jason.encode!(body))
  end

  defp to_mode("standard"), do: :standard
  defp to_mode("passthrough"), do: :passthrough
  defp to_mode(_), do: :invalid

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

  defp decode_rules(%{"rules" => raw}) when is_list(raw) do
    {:ok, Enum.map(raw, &decode_rule/1)}
  rescue
    e -> {:error, e}
  end

  defp decode_rules(_), do: {:error, :missing_rules_key}

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
