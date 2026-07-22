import Config

# Dev: listen on 4445 (litellm tier) / 4446 (front tier) so the live Python
# proxy on 4444/4443 is untouched.
config :ex_litellm,
  litellm_port: 4445,
  front_port: 4446
