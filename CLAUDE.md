# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Anime Triage Agent** — a seasonal anime recommendation system powered by a reasoning agent. Users get ranked, reasoned anime picks based on their preferences and the current season's catalog.

## Monorepo Structure

```
apps/api/                  FastAPI backend — agent logic, AniList/MAL integration, recommendation engine
apps/web/                  Next.js frontend — user preferences UI, recommendation display
packages/shared-schemas/   Shared Pydantic + Zod type definitions (source of truth for API contracts)
```

`packages/shared-schemas` is the contract layer: Python types live here as Pydantic models, TypeScript types as Zod schemas. When changing an API shape, update both.

## Commands

### API (FastAPI)
```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --reload           # dev server (http://localhost:8000)
pytest                              # all tests
pytest tests/test_agent.py -k foo   # single test by name
```

### Web (Next.js)
```bash
cd apps/web
npm install

npm run dev    # dev server (http://localhost:3000)
npm run build  # production build
npm run lint   # ESLint
```

## Architecture

### Reasoning Agent (`apps/api`)
The core of the system is a reasoning agent that scores and ranks seasonal anime. It:
1. Fetches the current season's catalog from an external API (AniList or MAL)
2. Runs user preferences through a Claude-powered triage loop using tool calls (search, filter, score)
3. Returns a ranked list with per-show reasoning

Agent logic lives in `apps/api/agent/`.

### API Layer (`apps/api`)
FastAPI routes expose the agent as HTTP endpoints. The `/recommend` endpoint is the primary entry point — accepts user preferences, returns the agent's ranked output.

### Frontend (`apps/web`)
Next.js app. Calls the FastAPI backend from Server Components (not the browser) to keep API keys server-side and avoid CORS.

### Shared Schemas (`packages/shared-schemas`)
Pydantic models (Python) and Zod schemas (TypeScript) mirror each other and define all request/response shapes. There is no codegen — keep them in sync manually when API contracts change.

## Conventions

- Ignore: `node_modules`, `__pycache__`, `.venv`, `dist`, `build`
- Environment variables: `.env` at repo root, loaded by both apps
