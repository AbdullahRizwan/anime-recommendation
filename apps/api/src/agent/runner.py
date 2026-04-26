import json
from datetime import date
from typing import Any

from openai import AsyncOpenAI

from ..domain.models import (
    AnimeEntry,
    RankedAnime,
    RecommendationRequest,
    RecommendationResponse,
)
from ..infrastructure.anilist_client import AniListClient
from .tools import get_tools

_MODEL = "llama-3.3-70b-versatile"
_MAX_TOKENS = 4096
_SYNOPSIS_LIMIT = 300


class RecommendationAgent:
    def __init__(self, llm: AsyncOpenAI, anilist: AniListClient) -> None:
        self._llm = llm
        self._anilist = anilist
        self._store: dict[int, AnimeEntry] = {}

    async def run(self, request: RecommendationRequest) -> RecommendationResponse:
        season, year = _resolve_season(request)
        user_msg = f"Recommend the top {request.top_n} anime for {season} {year}."
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": _system_prompt(request)},
            {"role": "user", "content": user_msg},
        ]
        final_content = ""

        while True:
            response = await self._llm.chat.completions.create(
                model=_MODEL,
                max_tokens=_MAX_TOKENS,
                tools=get_tools(),  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
            )
            choice = response.choices[0]

            if choice.finish_reason == "stop" or not choice.message.tool_calls:
                final_content = choice.message.content or ""
                break

            messages.append({
                "role": "assistant",
                "content": choice.message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ],
            })

            for tc in choice.message.tool_calls:
                result = await self._dispatch(
                    tc.function.name, json.loads(tc.function.arguments)
                )
                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": result}
                )

        return _parse_response(final_content, season, year)

    async def _dispatch(self, name: str, inputs: dict[str, Any]) -> str:
        if name == "get_seasonal_anime":
            season = str(inputs["season"])
            year = int(str(inputs["year"]))
            anime_list = await self._anilist.get_seasonal(season, year)
            self._store = {a.id: a for a in anime_list}
            return json.dumps([_to_dict(a) for a in anime_list])

        if name == "filter_anime":
            ids: list[int] = [int(i) for i in inputs["anime_ids"]]  # type: ignore[union-attr]
            include = {g.lower() for g in (inputs.get("include_genres") or [])}
            exclude = {g.lower() for g in (inputs.get("exclude_genres") or [])}
            max_ep: int | None = inputs.get("max_episodes")  # type: ignore[assignment]
            results = []
            for aid in ids:
                a = self._store.get(aid)
                if not a:
                    continue
                genres = {g.lower() for g in a.genres}
                if include and not include & genres:
                    continue
                if exclude and exclude & genres:
                    continue
                if max_ep and a.episodes and a.episodes > max_ep:
                    continue
                results.append(a)
            return json.dumps([_to_dict(a) for a in results])

        if name == "rank_anime":
            ids = [int(i) for i in inputs["anime_ids"]]  # type: ignore[union-attr]
            top_n = int(str(inputs["top_n"]))
            picks = [self._store[aid] for aid in ids if aid in self._store][:top_n]
            return json.dumps([_to_dict(a) for a in picks])

        raise ValueError(f"Unknown tool: {name}")


def _to_dict(a: AnimeEntry) -> dict[str, object]:
    return {
        "id": a.id,
        "title": a.title,
        "genres": a.genres,
        "synopsis": a.synopsis[:_SYNOPSIS_LIMIT],
        "score": a.score,
        "episodes": a.episodes,
        "status": a.status,
    }


def _resolve_season(request: RecommendationRequest) -> tuple[str, int]:
    if request.season and request.year:
        return request.season, request.year
    today = date.today()
    month = today.month
    season = (
        "WINTER" if month <= 3 else
        "SPRING" if month <= 6 else
        "SUMMER" if month <= 9 else
        "FALL"
    )
    return season, today.year


def _system_prompt(request: RecommendationRequest) -> str:
    prefs = request.preferences
    return (
        "You are an anime triage agent. Use the available tools to:\n"
        "1. Fetch the seasonal catalog with get_seasonal_anime\n"
        "2. Optionally filter with filter_anime\n"
        "3. Call rank_anime with your top picks\n"
        "4. Respond ONLY with valid JSON — no markdown, no extra text:\n\n"
        '{"season":"WINTER","year":2025,"reasoning_summary":"...","recommendations":['
        '{"id":1,"title":"...","rank":1,"score":8.5,"reasoning":"..."}'
        "]}\n\n"
        f"User likes: {', '.join(prefs.liked_genres) or 'no preference'}\n"
        f"User dislikes: {', '.join(prefs.disliked_genres) or 'none'}\n"
        f"Notes: {prefs.notes or 'none'}"
    )


def _parse_response(content: str, season: str, year: int) -> RecommendationResponse:
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    data: dict[str, Any] = json.loads(text.strip())
    return RecommendationResponse(
        season=data.get("season", season),
        year=data.get("year", year),
        reasoning_summary=data.get("reasoning_summary", ""),
        recommendations=[
            RankedAnime(
                id=int(r["id"]),
                title=str(r["title"]),
                rank=int(r["rank"]),
                score=float(r["score"]),
                reasoning=str(r["reasoning"]),
            )
            for r in data.get("recommendations", [])
        ],
    )


async def run_recommendation_agent(
    client: AsyncOpenAI,
    anilist: AniListClient,
    request: RecommendationRequest,
) -> RecommendationResponse:
    return await RecommendationAgent(client, anilist).run(request)
