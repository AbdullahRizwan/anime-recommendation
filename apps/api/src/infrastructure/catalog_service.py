from src.domain.models import AnimeEntry
from src.infrastructure.anilist_client import AniListClient
from src.infrastructure.anime_repository import AnimeRepository


def _search_cache_key(
    genres: list[str] | None, allow_explicit: bool, per_page: int
) -> str:
    g = "|".join(sorted(g.lower() for g in (genres or [])))
    return f"genres:{g}::explicit:{allow_explicit}::n:{per_page}"


class CatalogService:
    """Cache-aware catalog fetcher. Reads from DB; falls back to AniList on miss."""

    def __init__(self, anilist: AniListClient, repo: AnimeRepository) -> None:
        self._anilist = anilist
        self._repo = repo

    async def get_seasonal(
        self, season: str, year: int, allow_explicit: bool = False
    ) -> list[AnimeEntry]:
        cached = await self._repo.get_seasonal(season, year)
        if cached is not None:
            return cached
        fresh = await self._anilist.get_seasonal(season, year, allow_explicit=allow_explicit)
        await self._repo.store_seasonal(season, year, fresh)
        return fresh

    async def search_all(
        self,
        genres: list[str] | None = None,
        per_page: int = 50,
        allow_explicit: bool = False,
    ) -> list[AnimeEntry]:
        key = _search_cache_key(genres, allow_explicit, per_page)
        cached = await self._repo.get_search_cache(key)
        if cached is not None:
            return cached
        fresh = await self._anilist.search_all(
            genres=genres, per_page=per_page, allow_explicit=allow_explicit
        )
        await self._repo.store_search_cache(key, fresh)
        return fresh
