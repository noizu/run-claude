defmodule RunClaudeWeb.MainLayout do
  @moduledoc """
  Root layout for the run-claude landing page — head (SEO + OG), sticky header
  nav, footer. Dark-first typographic dev-tool theme; tokens in
  /assets/css/site.css. Copy source of truth: web/COPY.md.
  """

  use Hologram.Component

  def template do
    ~HOLO"""
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>run-claude — Claude Code. Your models.</title>
        <meta
          name="description"
          content="run-claude routes Claude Code and OpenCode through a local, self-healing model gateway: map opus/sonnet/haiku/fable tiers to 145+ models across ~26 provider profiles. Your keys, your machine, OAuth passthrough for your Claude subscription."
        />
        <meta property="og:type" content="website" />
        <meta property="og:title" content="run-claude — Claude Code. Your models." />
        <meta
          property="og:description"
          content="Keep the Claude Code UX, swap the economics: per-directory model routing through a localhost gateway. 145+ models, ~26 profiles, your keys, no cloud middleman."
        />
        <meta property="og:url" content="https://run-claude.therobotlives.com/" />
        <meta name="twitter:card" content="summary" />
        <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=JetBrains+Mono:wght@400;500;700&amp;display=swap"
          rel="stylesheet"
        />
        <link rel="stylesheet" href="/assets/css/site.css" />
        <Hologram.UI.Runtime />
      </head>
      <body>
        <a class="skip-link" href="#main">Skip to content</a>

        <header class="site-header">
          <div class="container header-inner">
            <a class="brand" href="#top" aria-label="run-claude home">
              <span class="brand-mark" aria-hidden="true">$</span>
              <span class="brand-name">run-claude</span>
            </a>
            <nav class="site-nav" aria-label="Primary">
              <a href="#tiers">Tiers</a>
              <a href="#how">How it works</a>
              <a href="#faq">FAQ</a>
              <a class="btn btn-primary btn-sm" href="#install">Install</a>
            </nav>
          </div>
        </header>

        <main id="main">
          <slot />
        </main>

        <footer class="site-footer">
          <div class="container footer-inner">
            <p class="footer-brand">run-claude — a noizu.com project</p>
            <p class="footer-line">
              <a href="https://github.com/noizu/run-claude">GitHub</a> ·
              <a href="https://github.com/noizu/run-claude/blob/main/LICENSE">MIT licensed</a> ·
              This site is Elixir Hologram. · © 2026
            </p>
          </div>
        </footer>
      </body>
    </html>
    """
  end
end
