import json
from dataclasses import dataclass, field

from pydantic_ai import RunContext

from ..domain.models import AnimeEntry, RecommendationRequest
from ..infrastructure.catalog_service import CatalogService

_SYNOPSIS_LIMIT = 300


@dataclass
class Deps:
    catalog: CatalogService
    request: RecommendationRequest
    season: str
    year: int
    store: dict[int, AnimeEntry] = field(default_factory=dict)


async def get_seasonal_anime(ctx: RunContext[Deps], season: str, year: int) -> str:
    """Fetch seasonal anime catalog from AniList. Season must be WINTER, SPRING, SUMMER, or FALL."""
    anime_list = await ctx.deps.catalog.get_seasonal(season.upper(), year)
    ctx.deps.store = {a.id: a for a in anime_list}
    return json.dumps([_to_dict(a) for a in anime_list])


async def search_all_anime(
    ctx: RunContext[Deps],
    genres: list[str] | None = None,
    per_page: int = 50,
) -> str:
    """Search AniList's full catalog (all years) filtered by genre, sorted by score.
    Use this when the user wants classic or highly-rated anime beyond the current season."""
    anime_list = await ctx.deps.catalog.search_all(genres=genres, per_page=per_page)
    for a in anime_list:
        ctx.deps.store[a.id] = a
    return json.dumps([_to_dict(a) for a in anime_list])


async def filter_anime(
    ctx: RunContext[Deps],
    anime_ids: list[int],
    include_genres: list[str] | None = None,
    exclude_genres: list[str] | None = None,
    synopsis_keywords: list[str] | None = None,
    max_episodes: int | None = None,
) -> str:
    """Filter an anime list by genres, synopsis keywords, or episode count.
    synopsis_keywords checks if any keyword appears in the description (case-insensitive)."""
    include = {g.lower() for g in (include_genres or [])}
    exclude_set = {g.lower() for g in (exclude_genres or [])}
    kw = [k.lower() for k in (synopsis_keywords or [])]
    results = []
    for aid in anime_ids:
        a = ctx.deps.store.get(aid)
        if not a:
            continue
        genres = {g.lower() for g in a.genres}
        if include and not include & genres:
            continue
        if exclude_set and exclude_set & genres:
            continue
        if max_episodes and a.episodes and a.episodes > max_episodes:
            continue
        synopsis_lower = a.synopsis.lower()
        if kw and not any(k in synopsis_lower for k in kw):
            continue
        results.append(a)
    return json.dumps([_to_dict(a) for a in results])


async def rank_anime(
    ctx: RunContext[Deps],
    anime_ids: list[int],
    top_n: int,
) -> str:
    """Get details for the model's top picks to rank."""
    picks = [ctx.deps.store[aid] for aid in anime_ids if aid in ctx.deps.store][:top_n]
    return json.dumps([_to_dict(a) for a in picks])


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
