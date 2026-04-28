from src.domain.models import AnimeEntry
from src.infrastructure.anilist_client import AniListClient
from src.infrastructure.anime_repository import AnimeRepository


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

    async def search_all(
        self,
        genres: list[str] | None = None,
        per_page: int = 50,
    ) -> list[AnimeEntry]:
        return await self._anilist.search_all(genres=genres, per_page=per_page)
