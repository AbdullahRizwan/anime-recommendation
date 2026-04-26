# Anime Triage Agent

A seasonal anime recommendation system powered by a reasoning agent. Give it your genre preferences and it fetches the current season's catalog, filters it, and returns a ranked list with per-show reasoning.

## Stack

| Layer | Tech |
|---|---|
| API | FastAPI, Python 3.13, uv |
| Agent | Groq (`llama-3.3-70b-versatile`) via OpenAI-compatible SDK |
| Anime data | AniList GraphQL API (free, no auth) |
| Frontend | Next.js 15, App Router, Tailwind CSS, shadcn/ui |
| Database | Postgres 17 + pgvector |
| Schemas | Pydantic (Python) + Zod (TypeScript) |

## Getting Started

### Prerequisites
- [uv](https://astral.sh/uv) — Python package manager
- [Bun](https://bun.sh) — JavaScript runtime
- [Docker Desktop](https://www.docker.com/products/docker-desktop) — for Postgres
- A free [Groq API key](https://console.groq.com)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/AbdullahRizwan/anime-recommendation.git
cd anime-recommendation

# 2. Configure environment
cp .env.example .env
# Edit .env and set GROQ_API_KEY=gsk_...

# 3. Start Postgres
docker compose up -d

# 4. Install dependencies
bun install
cd apps/api && uv sync --dev && cd ../..
```

### Running

```bash
# API (http://localhost:8000)
cd apps/api && uv run uvicorn src.main:app --reload

# Web (http://localhost:3000)
bun run dev:web
```

### Try it

```bash
curl -s -X POST http://localhost:8000/api/v1/recommend/ \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": {
      "liked_genres": ["Action", "Fantasy"],
      "disliked_genres": ["Ecchi"]
    },
    "top_n": 5
  }' | python3 -m json.tool
```

## Project Structure

```
apps/
  api/                  FastAPI backend
    src/
      agent/            Groq tool-call loop (runner + tools)
      application/      Service layer
      domain/           Pydantic models
      infrastructure/   AniList client, database
      presentation/     FastAPI routers
  web/                  Next.js frontend
packages/
  shared-schemas/       Pydantic + Zod schemas (API contract)
```

## How the Agent Works

1. Receives user preferences via `POST /api/v1/recommend/`
2. Calls `get_seasonal_anime` tool → fetches catalog from AniList
3. Calls `filter_anime` tool → narrows by genre/episode preferences
4. Calls `rank_anime` tool → retrieves details for top picks
5. Returns a ranked list with reasoning for each show
