# Anime Triage Agent

A seasonal anime recommendation system powered by a reasoning agent. Give it your genre preferences (and free-form notes), and it searches AniList's catalog — seasonal or all-time — and returns a ranked list with per-show reasoning. Progress streams back live over SSE as the agent works.

## Stack

| Layer | Tech |
|---|---|
| API | FastAPI, Python 3.13, uv |
| Agent | OpenAI (`gpt-4o-mini`) via pydantic-ai |
| Anime data | AniList GraphQL API (free, no auth) |
| Frontend | Next.js 15, App Router, Tailwind CSS, shadcn/ui |
| Database | Postgres 17 (pgvector image; vector search not yet used) — caches the AniList catalog |
| Schemas | Pydantic (Python) + Zod (TypeScript) |

## Getting Started

### Prerequisites
- [uv](https://astral.sh/uv) — Python package manager
- [Bun](https://bun.sh) — JavaScript runtime
- [Docker Desktop](https://www.docker.com/products/docker-desktop) — for Postgres
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/AbdullahRizwan/anime-recommendation.git
cd anime-recommendation

# 2. Configure environment
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...

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
      "disliked_genres": ["Ecchi"],
      "notes": "I love slow-burn worldbuilding and morally grey leads"
    },
    "top_n": 5
  }' | python3 -m json.tool
```

For live progress, `POST /api/v1/recommend/stream` returns the same result over
Server-Sent Events, emitting one event per tool call followed by a final result.
This is what the web UI consumes. Omit `season`/`year` to search all-time, or set
them (e.g. `"season": "SPRING", "year": 2026`) to restrict to a season.

## Project Structure

```
apps/
  api/                  FastAPI backend
    src/
      agent/            pydantic-ai agent (agent, runner, tools)
      application/      Service layer
      domain/           Pydantic models + exceptions
      infrastructure/   AniList client, catalog service, Postgres cache
      routers/          FastAPI routers
  web/                  Next.js frontend
packages/
  shared-schemas/       Pydantic + Zod schemas (API contract)
```

## How the Agent Works

The agent has a single self-contained tool, `search_catalog`, which fetches,
filters, sorts, and returns full details for matching anime in one call. There is
no separate fetch/filter/rank step — each call returns everything the agent needs.

1. Receives user preferences via `POST /api/v1/recommend/` (or `/stream`).
2. Runs as many `search_catalog` calls as it judges useful — e.g. one per liked
   genre, or a seasonal pass plus an all-time pass — to build a varied candidate
   pool. Each call can filter by genres, excluded genres, synopsis keywords,
   season, episode count, and minimum score.
3. Chooses and orders the best picks itself, weighing the user's notes — ranking is
   the model's judgment, not just the raw catalog score.
4. The runner enriches the output by id (authoritative titles, scores, cover
   images from the catalog) and returns a ranked list with per-show reasoning.

The system prompt is principle-based rather than a fixed recipe, so the agent
adapts its search strategy to each user instead of always walking the same path.
