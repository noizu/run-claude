defmodule ExLiteLLM.Proxy.Endpoint do
  @moduledoc """
  Root Plug router for the **LiteLLM tier** (dev :4445 → prod :4444).

  The OpenAI-compatible inference + admin surface that replaces the Python
  `litellm` proxy. Phase 2 wires: health/liveness/readiness (public), the root
  banner, master-key auth on the inference plane, and non-streaming
  `/v1/chat/completions`, `/v1/embeddings`, `/v1/models`. Remaining subsystems
  (model/key/team management, streaming, the admin plane) land in later phases;
  unknown routes answer an honest 501.
  """
  use Plug.Router

  alias ExLiteLLM.Proxy.{Auth, Health, Inference}

  plug(:match)

  # Parse JSON bodies once, up front, for the inference plane.
  plug(Plug.Parsers,
    parsers: [:json],
    pass: ["application/json"],
    json_decoder: Jason
  )

  plug(:stash_json_body)
  plug(:dispatch)

  # --- Public: root banner + health (no auth) ---
  get "/" do
    send_resp(conn, 200, "LiteLLM: RUNNING")
  end

  get("/health", do: Health.health(conn))
  get("/health/readiness", do: Health.readiness(conn))
  get("/health/liveliness", do: Health.liveness(conn))
  get("/health/liveness", do: Health.liveness(conn))

  # --- Inference plane (master-key auth) ---
  post "/v1/chat/completions", do: authed(conn, &Inference.chat_completions/1)
  post "/chat/completions", do: authed(conn, &Inference.chat_completions/1)
  post "/v1/embeddings", do: authed(conn, &Inference.embeddings/1)
  post "/embeddings", do: authed(conn, &Inference.embeddings/1)
  get "/v1/models", do: authed(conn, &Inference.models/1)
  get "/models", do: authed(conn, &Inference.models/1)

  # --- Fallthrough: not-yet-implemented endpoints answer honestly ---
  match _ do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(
      501,
      Jason.encode!(%{
        error: %{
          message: "endpoint not yet implemented in ex-litellm: #{conn.request_path}",
          type: "not_implemented",
          code: 501
        }
      })
    )
  end

  # --- plumbing ---

  # Run auth as an inline gate; if it halts (401), stop — else run the handler.
  defp authed(conn, handler) do
    conn = Auth.call(conn, [])
    if conn.halted, do: conn, else: handler.(conn)
  end

  # Copy the parsed body into assigns so controllers read it without touching
  # the (already consumed) conn body.
  defp stash_json_body(conn, _opts) do
    case conn.body_params do
      %Plug.Conn.Unfetched{} -> conn
      params when is_map(params) -> Plug.Conn.assign(conn, :json_body, params)
      _ -> conn
    end
  end
end
