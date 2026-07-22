import Config

# ex-litellm application defaults. Runtime values (ports, DB path, master key,
# config file) are resolved in runtime.exs / by the CLI from env + --flags so the
# escript behaves like the `litellm` binary.

config :ex_litellm,
  ecto_repos: [ExLiteLLM.Schema.Repo],
  # Default listener ports. Dev uses 4445/4446 so the live Python proxy on
  # 4444/4443 is never disturbed; cutover flips these to 4444/4443.
  litellm_port: 4445,
  front_port: 4446,
  host: "127.0.0.1"

# SQLite is the default backend — a single self-contained file, no container.
config :ex_litellm, ExLiteLLM.Schema.Repo,
  adapter: Ecto.Adapters.SQLite3,
  # Overridden at runtime from database_url / LITELLM_DATABASE_URL when given.
  database: Path.expand("~/.local/state/ex-litellm/ex_litellm.db"),
  pool_size: 10,
  journal_mode: :wal,
  busy_timeout: 5_000

config :logger, :console,
  format: "$time [$level] $message\n",
  metadata: [:tier, :request_id]

import_config "#{config_env()}.exs"
