defmodule ExLiteLLM.Gateway.Forwarder do
  @moduledoc """
  Upstream request forwarding for the gateway's passthrough targets (Anthropic
  or an arbitrary URL) — the reverse-proxy half of the old front proxy, now a
  shared helper.

  Handles hop-by-hop header stripping, the master-key-swap vs passthrough auth
  decision, and both buffered and SSE-streaming forwarding via `Req`.
  """

  import Plug.Conn
  require Logger

  alias ExLiteLLM.Runtime

  @hop_by_hop ~w(host connection keep-alive transfer-encoding te trailer upgrade content-length)
  @strip_resp ~w(content-encoding content-length transfer-encoding)

  @doc """
  Forward the current request to `base_url` and relay the response. `auth_mode`
  is `:master_key` (strip client auth, inject the LiteLLM master key) or
  `:passthrough` (keep original headers). Streams when the client asked for SSE.
  """
  @spec forward(Plug.Conn.t(), String.t(), :master_key | :passthrough, binary()) :: Plug.Conn.t()
  def forward(conn, base_url, auth_mode, raw_body) do
    url = base_url <> conn.request_path <> qs(conn)
    headers = forward_headers(conn, auth_mode)

    if streaming?(conn) do
      stream(conn, url, headers, raw_body)
    else
      buffered(conn, url, headers, raw_body)
    end
  end

  defp buffered(conn, url, headers, body) do
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
        error(conn, exc)
    end
  end

  defp stream(conn, url, headers, body) do
    conn = send_chunked(conn, 200)
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
      {:ok, _resp} -> conn_ref_get()
      {:error, exc} ->
        Logger.error("[gateway] stream forward error: #{inspect(exc)}")
        conn_ref_get()
    end
  end

  # --- headers ---

  defp forward_headers(conn, :master_key) do
    master = Runtime.get().master_key || ""

    conn.req_headers
    |> Enum.reject(fn {k, _v} -> String.downcase(k) in @hop_by_hop end)
    |> Enum.reject(fn {k, _v} -> String.downcase(k) == "authorization" end)
    |> Kernel.++([{"authorization", "Bearer " <> master}])
  end

  defp forward_headers(conn, :passthrough) do
    Enum.reject(conn.req_headers, fn {k, _v} -> String.downcase(k) in @hop_by_hop end)
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

  # --- helpers ---

  defp streaming?(conn) do
    case get_req_header(conn, "accept") do
      [accept | _] -> String.contains?(accept, "text/event-stream")
      _ -> false
    end
  end

  defp qs(%{query_string: ""}), do: ""
  defp qs(%{query_string: q}), do: "?" <> q

  defp method_atom(method), do: method |> String.downcase() |> String.to_atom()

  defp error(conn, exc) do
    Logger.error("[gateway] upstream forward error: #{inspect(exc)}")

    conn
    |> put_resp_content_type("application/json")
    |> send_resp(
      502,
      Jason.encode!(%{type: "error", error: %{type: "api_error", message: "upstream request failed"}})
    )
  end

  defp conn_ref_get, do: Process.get(:exll_fwd_conn)
  defp conn_ref_put(conn), do: (Process.put(:exll_fwd_conn, conn) && conn)
end
