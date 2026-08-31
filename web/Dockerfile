# syntax=docker/dockerfile:1.7
#
# run-claude landing — server-rendered Phoenix/Hologram app (NOT a static site).
# Final stage MUST be named `AS production` (deploy tooling depends on it).
# Cache policy mirrors the Timely backend image: hex/rebar/deps on BuildKit
# cache mounts; _build deliberately in the layer (Hologram bundler renames
# priv output across devices → EXDEV if _build were a cache mount).

ARG BASE_IMAGE="elixir:1.18.4-otp-28-slim"

FROM ${BASE_IMAGE} AS build

# Node 20+ required by the Hologram compiler (Elixir → JS bundles)
RUN apt-get update -y && \
    apt-get install -y build-essential git curl ca-certificates wget && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cross-arch emulation (QEMU / Rosetta) breaks BEAM's double-mapped RWX JIT
# pages and can corrupt compiler state during mix deps.compile.
ENV ERL_AFLAGS="+JMsingle true"

# Keep emulated builds below the scheduler/RSS cliff.
ENV ERL_FLAGS="+S 2:2"
ENV ELIXIR_ERL_OPTIONS="+S 2:2"

RUN mix local.hex --force && mix local.rebar --force

ENV MIX_ENV=prod

COPY mix.exs mix.lock ./
# deps.get is repeated in every deps-consuming RUN: gha layer-cache hits skip
# the earlier deps.get layer, and the gha exporter does NOT persist type=cache
# mounts, so a cold CI runner mounts an empty /app/deps and compile dies with
# "the dependency is not available". In-RUN deps.get is a no-op when the mount
# is warm and repopulates it when cold.
RUN --mount=type=cache,id=rcweb-mix-hex,target=/root/.hex,sharing=locked \
    --mount=type=cache,id=rcweb-mix-rebar,target=/root/.cache/rebar3,sharing=locked \
    --mount=type=cache,id=rcweb-mix-deps,target=/app/deps,sharing=locked \
    mix deps.get --only $MIX_ENV && \
    mkdir -p config

# Whole config dir: config.exs imports runtime.exs, which mix evaluates
# during deps.compile — so runtime.exs must exist before that step.
COPY config/ config/
RUN --mount=type=cache,id=rcweb-mix-hex,target=/root/.hex,sharing=locked \
    --mount=type=cache,id=rcweb-mix-rebar,target=/root/.cache/rebar3,sharing=locked \
    --mount=type=cache,id=rcweb-mix-deps,target=/app/deps,sharing=locked \
    mix deps.get --only $MIX_ENV && \
    MIX_OS_DEPS_COMPILE_PARTITION_COUNT=1 mix deps.compile

COPY lib lib
COPY app app
COPY priv priv

RUN --mount=type=cache,id=rcweb-mix-hex,target=/root/.hex,sharing=locked \
    --mount=type=cache,id=rcweb-mix-rebar,target=/root/.cache/rebar3,sharing=locked \
    --mount=type=cache,id=rcweb-mix-deps,target=/app/deps,sharing=locked \
    mix deps.get --only $MIX_ENV && \
    mix compile

RUN --mount=type=cache,id=rcweb-mix-hex,target=/root/.hex,sharing=locked \
    --mount=type=cache,id=rcweb-mix-rebar,target=/root/.cache/rebar3,sharing=locked \
    --mount=type=cache,id=rcweb-mix-deps,target=/app/deps,sharing=locked \
    mix deps.get --only $MIX_ENV && \
    mix release && cp -a /app/_build/${MIX_ENV}/rel/run_claude_web /app/release

FROM ${BASE_IMAGE} AS production

WORKDIR /app
RUN chown nobody /app && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends wget && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# HOLOGRAM_START=1 is required or Hologram routes 404.
ENV MIX_ENV=prod \
    HOLOGRAM_START=1 \
    PHX_HOST=run-claude.therobotlives.com

COPY --from=build --chown=nobody:root /app/release ./

USER nobody

EXPOSE 8150

HEALTHCHECK --interval=15s --timeout=3s --start-period=15s --retries=3 \
  CMD wget -qO- http://localhost:8150/healthz || exit 1

CMD ["bin/run_claude_web", "start"]
