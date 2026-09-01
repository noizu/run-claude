# PRD-07: run-claude Landing Page & Website

**Phase**: 7 | **Est**: 5 days | **Repo**: run-claude-website (separate)

## Context

run-claude needs a public-facing website for discovery, documentation, and community building.

---

## Target Audience

**Primary**: AI developers using Claude Code, Aider, Cursor who manage multiple LLM providers.
**Secondary**: DevOps engineers, open source contributors, enterprise teams.

## Tech Stack

- **Framework**: Astro (static, content-focused, fast)
- **Styling**: Tailwind CSS
- **Code blocks**: Shiki syntax highlighting
- **Diagrams**: Mermaid
- **Hosting**: Vercel (free for open source, CDN)
- **Analytics**: Plausible (privacy-friendly)

## Pages

### Home (`/`)
- Hero: "Directory-aware AI model routing"
- Problem statement + quick demo GIF
- Feature highlights (3-4 cards)
- Supported tools badges (Claude, Aider, Cursor)
- Quick install snippet
- CTA: Get Started / View on GitHub

### Features (`/features`)
- Directory-based profiles (automatic switching)
- 14+ built-in provider profiles
- Zero-config for popular tools
- Refcount-based lifecycle (no model thrashing)
- TimescaleDB message history

### Quick Start (`/docs/quick-start`)
- Install (pip, uv)
- Configure secrets
- Set up first project
- Verify with Claude Code

### Documentation (`/docs`)
- Links to ReadTheDocs for full docs
- Or embedded Astro content collection for docs

### Integrations (`/integrations`)
- Claude Code, Aider, Cursor setup guides
- Environment variable reference

### Community (`/community`)
- GitHub link, Discord, Contributing guide

## Marketing Plan

### Launch Channels
1. **Hacker News** — Show HN post
2. **Reddit** — r/LocalLLaMA, r/ClaudeAI, r/ArtificialIntelligence
3. **Dev.to** — Tutorial: "Managing 14 LLM providers without losing your mind"
4. **Newsletters** — TLDR, Ben's Bites, Superhuman AI
5. **X/Twitter** — Thread with GIF demo
6. **Discord** — Anthropic, LangChain communities

### Content Plan
- Blog post: "Stop paying for dev work — route to Cerebras"
- Tutorial: "Directory-aware AI model routing in 5 minutes"
- Video: 2-min demo on YouTube

### Success Metrics
- GitHub stars: 1000 in first month
- pip downloads: 500/week
- Website visitors: 5000 in first month
