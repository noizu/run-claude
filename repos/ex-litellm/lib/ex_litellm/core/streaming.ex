defmodule ExLiteLLM.Core.Streaming do
  @moduledoc """
  Server-Sent-Events streaming — litellm's `CustomStreamWrapper` +
  `BaseModelResponseIterator`.

  Two responsibilities:

    * **Outbound parse** — take the raw byte stream from the upstream provider,
      split it into SSE events (`data: {...}\\n\\n`), JSON-decode each `data:`
      payload, and hand it to the adapter's `chunk_parser/1` to normalize into a
      `GenericStreamingChunk`.
    * **Inbound emit** — turn each normalized chunk into an OpenAI
      `chat.completion.chunk` SSE frame and chunk it back to the client, closing
      with `data: [DONE]`.

  `stream/4` drives the whole thing over a `Plug.Conn` using `Req`'s streaming
  response body, writing frames as they arrive with `Plug.Conn.chunk/2`.
  """

  import Plug.Conn
  require Logger

  alias ExLiteLLM.Error
  alias ExLiteLLM.Providers.Adapter.Request

  @doc """
  Stream a chat completion to the client as OpenAI SSE.

  Sets up the chunked response, opens the upstream streaming request via the
  adapter + `Req`, parses each provider event through `adapter.chunk_parser/1`,
  emits OpenAI chunk frames, and terminates with `[DONE]`. Returns the conn.
  """
  @spec stream(Plug.Conn.t(), module(), Request.t(), map()) :: Plug.Conn.t()
  def stream(conn, adapter, %Request{} = req, upstream_body) do
    with {:ok, headers} <- adapter.validate_environment(req, %{}) do
      url = adapter.get_complete_url(req)
      chunk_id = "chatcmpl-" <> rand()
      created = System.system_time(:second)

      conn =
        conn
        |> put_resp_content_type("text/event-stream")
        |> put_resp_header("cache-control", "no-cache")
        |> send_chunked(200)

      state = %{
        conn: conn,
        adapter: adapter,
        req: req,
        chunk_id: chunk_id,
        created: created,
        buffer: "",
        finished: false
      }

      final = run_stream(url, headers, upstream_body, req, state)
      finalize(final)
    else
      {:error, %Error{} = e} -> send_error(conn, e)
    end
  end

  # --- upstream streaming via Req ---

  defp run_stream(url, headers, body, %Request{litellm_params: lp}, state) do
    timeout = stream_timeout(lp)

    # Seed the per-call streaming state before Req's into/2 callback fires; the
    # callback can only thread {req, resp}, so our mutable frame state lives in
    # the process dictionary (each request runs in its own process).
    state_ref_put(Map.put_new(state, :error, nil))

    result =
      Req.post(url,
        headers: Map.to_list(headers),
        json: body,
        receive_timeout: timeout,
        retry: false,
        into: fn {:data, data}, {req, resp} ->
          state_ref_put(consume(state_ref_get(), data))
          {:cont, {req, resp}}
        end
      )

    case result do
      {:ok, _resp} -> state_ref_get()
      {:error, exc} -> %{state_ref_get() | error: stream_exc(exc)}
    end
  end

  # Feed a raw byte blob into the SSE line parser, emitting OpenAI frames.
  defp consume(state, data) do
    {events, rest} = split_sse(state.buffer <> data)
    state = %{state | buffer: rest}

    Enum.reduce(events, state, fn event, acc ->
      case parse_event(event) do
        :skip -> acc
        :done -> %{acc | finished: true}
        {:data, payload} -> handle_payload(acc, payload)
      end
    end)
  end

  defp handle_payload(state, payload) do
    if state.finished do
      state
    else
      chunk = state.adapter.chunk_parser(payload)
      emit(state, chunk)
    end
  end

  defp emit(state, :done), do: %{state | finished: true}

  defp emit(state, chunk) when is_map(chunk) do
    frame = openai_chunk_frame(state, chunk)

    case chunk(state.conn, "data: " <> Jason.encode!(frame) <> "\n\n") do
      {:ok, conn} -> %{state | conn: conn, finished: chunk.is_finished || state.finished}
      {:error, _} -> %{state | finished: true}
    end
  end

  # --- OpenAI chunk shaping ---

  defp openai_chunk_frame(state, chunk) do
    delta =
      %{}
      |> put_if(:content, blank_to_nil(chunk.text))
      |> put_if(:tool_calls, chunk.tool_use)

    %{
      id: state.chunk_id,
      object: "chat.completion.chunk",
      created: state.created,
      model: state.req.model,
      choices: [
        %{
          index: chunk.index,
          delta: delta,
          finish_reason: chunk.finish_reason
        }
      ]
    }
    |> maybe_usage(chunk.usage)
  end

  defp maybe_usage(frame, nil), do: frame
  defp maybe_usage(frame, usage), do: Map.put(frame, :usage, usage)

  defp finalize(%{error: %Error{} = e, conn: conn}), do: send_error_frame(conn, e)

  defp finalize(state) do
    {:ok, conn} = chunk(state.conn, "data: [DONE]\n\n")
    conn
  end

  # --- SSE parsing ---

  # Split a buffer into complete SSE events (separated by blank lines) + remainder.
  defp split_sse(buffer) do
    parts = String.split(buffer, ~r/\r?\n\r?\n/)

    case Enum.reverse(parts) do
      [last | rest] -> {Enum.reverse(rest), last}
      [] -> {[], ""}
    end
  end

  # An SSE event may have multiple `data:` lines; join them, strip the prefix.
  defp parse_event(event) do
    data =
      event
      |> String.split(~r/\r?\n/)
      |> Enum.filter(&String.starts_with?(&1, "data:"))
      |> Enum.map(&String.trim_leading(String.replace_prefix(&1, "data:", "")))
      |> Enum.join("\n")

    cond do
      data == "" -> :skip
      String.trim(data) == "[DONE]" -> :done
      true -> decode_data(data)
    end
  end

  defp decode_data(data) do
    case Jason.decode(data) do
      {:ok, payload} -> {:data, payload}
      {:error, _} -> :skip
    end
  end

  # --- error paths ---

  defp send_error(conn, %Error{} = e) do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(e.status, Jason.encode!(Error.to_body(e)))
  end

  defp send_error_frame(conn, %Error{} = e) do
    {:ok, conn} = chunk(conn, "data: " <> Jason.encode!(Error.to_body(e)) <> "\n\n")
    {:ok, conn} = chunk(conn, "data: [DONE]\n\n")
    conn
  end

  # --- helpers ---

  defp put_if(map, _key, nil), do: map
  defp put_if(map, key, value), do: Map.put(map, key, value)

  defp blank_to_nil(""), do: nil
  defp blank_to_nil(v), do: v

  defp stream_timeout(%{"stream_timeout" => t}) when is_number(t), do: round(t * 1000)
  defp stream_timeout(%{"timeout" => t}) when is_number(t), do: round(t * 1000)
  defp stream_timeout(_), do: 600_000

  defp stream_exc(%{__struct__: _} = exc),
    do: Error.new(502, "upstream stream failed: #{Exception.message(exc)}", type: "api_error")

  defp stream_exc(other),
    do: Error.new(502, "upstream stream failed: #{inspect(other)}", type: "api_error")

  defp rand, do: 16 |> :crypto.strong_rand_bytes() |> Base.url_encode64(padding: false)

  # Per-call streaming state carried across Req's into/2 callback via the
  # process dictionary (each request runs in its own process).
  defp state_ref_get, do: Process.get(:exll_stream_state)
  defp state_ref_put(state), do: Process.put(:exll_stream_state, state)
end
