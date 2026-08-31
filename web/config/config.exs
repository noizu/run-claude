import Config

config :run_claude_web, RunClaudeWeb.Endpoint,
  url: [host: "localhost"],
  adapter: Bandit.PhoenixAdapter,
  render_errors: [formats: [html: RunClaudeWeb.ErrorHTML], layout: false],
  pubsub_server: RunClaudeWeb.PubSub,
  live_view: [signing_salt: "runClaudeWeb"],
  secret_key_base: "tW7qz3vP9mLxK2nRb8sYcH5jFd4eAg6uQi1oZwXtSyNm0pCkEhVaJrLsGdMfBuT3",
  http: [ip: {127, 0, 0, 1}, port: 8150],
  server: true

config :phoenix, :json_library, Jason

config :logger, level: :info

# Runtime overrides (PORT / BIND_IP / PHX_HOST) — prod only, see runtime.exs.
import_config "runtime.exs"
