defmodule RunClaudeWeb.RequestTest do
  use ExUnit.Case, async: false
  import Phoenix.ConnTest

  @endpoint RunClaudeWeb.Endpoint

  test "GET / renders the landing page with the hero headline" do
    conn = get(build_conn(), "/")
    assert conn.status == 200
    assert conn.resp_body =~ "Claude Code. Your models."
  end

  test "GET / includes SEO head tags" do
    conn = get(build_conn(), "/")
    body = conn.resp_body

    assert body =~ "<title>run-claude — Claude Code. Your models.</title>"
    assert body =~ ~r/name="description" content="run-claude routes Claude Code/
    assert body =~ "og:title"
  end

  test "GET / includes benefits, tier table, how-it-works, FAQ, and CTA copy" do
    conn = get(build_conn(), "/")
    body = conn.resp_body

    assert body =~ "Claude Code, your models"
    assert body =~ "Your subscription, where it makes sense"
    assert body =~ "Local gateway, no middleman"
    assert body =~ "Tier mappings are one YAML stanza"
    assert body =~ "claude-opus-4-8"
    assert body =~ "glm-5.3-flash (low)"
    assert body =~ "How it works"
    assert body =~ "Do my API keys leave my machine?"
    assert body =~ "the license?"
    assert body =~ "run-claude secrets init --generate"
    assert body =~ "Install in one command"
  end

  test "GET / includes footer attribution" do
    conn = get(build_conn(), "/")
    body = conn.resp_body

    assert body =~ "a noizu.com project"
    assert body =~ "https://github.com/noizu/run-claude"
    assert body =~ "This site is Elixir Hologram."
  end

  test "static assets are served" do
    conn = get(build_conn(), "/assets/css/site.css")
    assert conn.status == 200
  end
end
