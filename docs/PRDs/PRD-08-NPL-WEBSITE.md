# PRD-08: NPL (Noizu Prompt Lingua) Landing Page & Website

**Phase**: 7 | **Est**: 5 days | **Repo**: npl-website (separate)

## Context

Noizu Prompt Lingua (NPL) is a structured reflection protocol for AI agents. It needs a public-facing website with an interactive playground for the spec, parser libraries, and community.

---

## Target Audience

**Primary**: AI engineers building agentic systems, prompt engineers.
**Secondary**: AI researchers, open source contributors, enterprise teams.

## Tech Stack

- **Framework**: Next.js + MDX (SSR, interactive components)
- **Styling**: Tailwind CSS + shadcn/ui
- **Playground**: Monaco Editor (code editing) + real-time NPL parser
- **Hosting**: Vercel
- **Analytics**: Plausible

## Pages

### Home (`/`)
- Hero: "Structured Reflection for AI Agents"
- Interactive demo: NPL reflection block → parsed output + quality score
- Problem/solution framing
- CTA: Read the Spec / Try Playground

### Specification (`/spec/v1`)
- Full grammar reference
- Block types: reflection, check-in, assumption, plan
- Emoji taxonomy with meanings
- Parsing rules
- Extension points

### Playground (`/playground`)
- Monaco editor on left (write NPL blocks)
- Parsed output on right (categories, score, validation)
- Example templates dropdown
- Export: JSON, TypeScript interface, Python dataclass

### Why NPL? (`/why`)
- Problem: unstructured AI outputs
- Solution: machine-parseable reflection blocks
- Benefits for: single agents, multi-agent systems, training data, CI/CD

### Tooling (`/tools`)
- Parser libraries: Python (`npl-parser`), TypeScript (`@npl/parser`)
- Editor extensions: VSCode
- Integrations: Claude Code, run-claude eval system

### Community (`/community`)
- GitHub org, RFC process, showcase

## Marketing Plan

### Launch Channels
1. **Product Hunt** — Launch day submission
2. **Hacker News** — "Show HN: A lingua franca for AI agent self-review"
3. **Dev.to** — Tutorial series (4 parts)
4. **Reddit** — r/MachineLearning, r/PromptEngineering
5. **arXiv** — Paper: "NPL: A Structured Reflection Protocol for LLM Agents"
6. **Conferences** — EMNLP/ACL workshop submissions

### Content Plan
- Tutorial series: Why agents need structure → Implementing NPL → Building evals → Training data
- Case study: "How run-claude uses NPL for quality gates"
- Video: Spec walkthrough + playground demo

### Launch Timeline
- Month 1: Spec v1.0, parser libs, website, GitHub org
- Month 2: Dev.to tutorials, HN launch, Product Hunt
- Month 3: arXiv paper, conference proposals, partner integrations
- Month 4+: Case studies, enterprise adoption, spec v2 RFC

### Success Metrics
- GitHub stars (org-wide): 2000 in 6 months
- Parser downloads: 1000/week
- Playground unique visitors: 10000 in 3 months
