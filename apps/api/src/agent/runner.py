import asyncio
from collections.abc import AsyncIterator
from datetime import date

from pydantic_ai.agent import AgentRunResult

from src.agent.agent import agent
from src.agent.tools import Deps
from src.domain.exceptions import AgentError, AniListError, DatabaseError
from src.domain.models import (
    AnimeEntry,
    RankedAnime,
    RecommendationRequest,
    RecommendationResponse,
)
from src.infrastructure.catalog_service import CatalogService

_TIMEOUT_SECONDS = 120


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


def _build_prompt(request: RecommendationRequest, season: str, year: int) -> str:
    if request.season and request.year:
        return f"Recommend the top {request.top_n} anime airing in {season} {year}."
    return f"Recommend the top {request.top_n} anime based on the user's preferences."


def _enrich(
    response: RecommendationResponse, store: dict[int, AnimeEntry]
) -> RecommendationResponse:
    """Overwrite model-transcribed fields with authoritative catalog values.

    The model picks ids, ranks, and reasoning; titles, scores, and cover images are
    taken from the store so a mistyped URL or hallucinated score never reaches the UI.
    """
    enriched: list[RankedAnime] = []
    for rec in response.recommendations:
        entry = store.get(rec.id)
        if entry is None:
            enriched.append(rec)
            continue
        enriched.append(
            rec.model_copy(
                update={
                    "title": entry.title,
                    "score": entry.score if entry.score is not None else rec.score,
                    "cover_image": entry.cover_image,
                }
            )
        )
    return response.model_copy(update={"recommendations": enriched})


async def run_recommendation_agent(
    catalog: CatalogService,
    request: RecommendationRequest,
) -> RecommendationResponse:
    season, year = _resolve_season(request)
    deps = Deps(catalog=catalog, request=request, season=season, year=year)
    prompt = _build_prompt(request, season, year)
    try:
        result = await asyncio.wait_for(
            agent.run(prompt, deps=deps), timeout=_TIMEOUT_SECONDS
        )
    except TimeoutError:
        raise AgentError(
            f"Agent timed out after {_TIMEOUT_SECONDS} seconds."
        ) from None
    except (AniListError, DatabaseError):
        raise
    except Exception as e:
        raise AgentError(str(e)) from e
    return _enrich(result.output, deps.store)


async def run_recommendation_agent_stream(
    catalog: CatalogService,
    request: RecommendationRequest,
) -> AsyncIterator[dict[str, object]]:
    """Run the agent, yielding progress events as tools fire, then a final result.

    Event shapes:
      {"type": "tool", "tool": str, "status": "started"|"finished", "label": str, ...}
      {"type": "complete", "data": <RecommendationResponse dict>}
      {"type": "error", "message": str}
    """
    season, year = _resolve_season(request)
    queue: asyncio.Queue[dict[str, object]] = asyncio.Queue()
    deps = Deps(
        catalog=catalog, request=request, season=season, year=year, events=queue
    )
    prompt = _build_prompt(request, season, year)

    agent_task: asyncio.Task[AgentRunResult[RecommendationResponse]]
    agent_task = asyncio.create_task(agent.run(prompt, deps=deps))
    try:
        while True:
            get_task: asyncio.Task[dict[str, object]] = asyncio.create_task(queue.get())
            done, _ = await asyncio.wait(
                {get_task, agent_task},
                return_when=asyncio.FIRST_COMPLETED,
                timeout=_TIMEOUT_SECONDS,
            )
            if get_task in done:
                yield get_task.result()
            else:
                get_task.cancel()

            if agent_task in done:
                while not queue.empty():
                    yield queue.get_nowait()
                break

            if not done:  # overall timeout with no progress
                agent_task.cancel()
                yield {
                    "type": "error",
                    "message": f"Agent timed out after {_TIMEOUT_SECONDS} seconds.",
                }
                return

        result = agent_task.result()
        enriched = _enrich(result.output, deps.store)
        yield {"type": "complete", "data": enriched.model_dump()}
    except (AniListError, DatabaseError) as e:
        yield {"type": "error", "message": str(e)}
    except Exception as e:  # noqa: BLE001 — surface any agent failure to the client
        yield {"type": "error", "message": str(e)}
    finally:
        if not agent_task.done():
            agent_task.cancel()
