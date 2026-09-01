import Config

# Test overrides — no HTTP listener; requests go through Phoenix.ConnTest.
config :run_claude_web, RunClaudeWeb.Endpoint,
  server: false,
  http: [ip: {127, 0, 0, 1}, port: 8151]
