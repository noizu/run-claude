import Config

# Prod: cutover ports — the front tier on 4443 and the litellm tier on 4444,
# exactly where run-claude expects the Python proxies today.
config :ex_litellm,
  litellm_port: 4444,
  front_port: 4443
