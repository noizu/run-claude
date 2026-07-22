import Config

# Test: in-memory SQLite, ports that won't collide with a running dev/prod proxy.
config :ex_litellm,
  litellm_port: 14_445,
  front_port: 14_446,
  # Don't auto-start the HTTP listeners during unit tests unless a test opts in.
  start_servers: false

config :ex_litellm, ExLiteLLM.Schema.Repo,
  database: ":memory:",
  pool: Ecto.Adapters.SQL.Sandbox,
  pool_size: 5

config :logger, level: :warning
