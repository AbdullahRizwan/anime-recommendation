from ..domain.models import AnimeEntry
from .anilist_client import AniListClient
from .anime_repository import AnimeRepository


class CatalogService:
    """Cache-aware catalog fetcher. Reads from DB; falls back to AniList on miss."""

    def __init__(self, anilist: AniListClient, repo: AnimeRepository) -> None:
        self._anilist = anilist
        self._repo = repo

    async def get_seasonal(self, season: str, year: int) -> list[AnimeEntry]:
        cached = await self._repo.get_seasonal(season, year)
        if cached is not None:
            return cached
        fresh = await self._anilist.get_seasonal(season, year)
        await self._repo.store_seasonal(season, year, fresh)
        return fresh
