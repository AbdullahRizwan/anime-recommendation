import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.exceptions import DatabaseError
from src.domain.models import AnimeEntry
from src.infrastructure.orm_models import SearchCacheORM, SeasonalAnimeORM

_SEARCH_TTL = timedelta(hours=24)


class AnimeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        # A single AsyncSession cannot be used by concurrent coroutines. The agent
        # may fire several search_catalog tool calls in parallel, so serialise every
        # session operation. The slow AniList HTTP calls live in CatalogService,
        # outside this lock, and remain concurrent.
        self._lock = asyncio.Lock()

    async def get_seasonal(
        self, season: str, year: int
    ) -> list[AnimeEntry] | None:
        async with self._lock:
            try:
                result = await self._session.execute(
                    select(SeasonalAnimeORM).where(
                        SeasonalAnimeORM.season == season,
                        SeasonalAnimeORM.year == year,
                    )
                )
            except SQLAlchemyError as e:
                raise DatabaseError(f"DB unavailable: {e}") from e
            rows = result.scalars().all()
        if not rows:
            return None
        return [_seasonal_to_domain(row) for row in rows]

    async def store_seasonal(
        self, season: str, year: int, anime: list[AnimeEntry]
    ) -> None:
        async with self._lock:
            try:
                for a in anime:
                    row = SeasonalAnimeORM(
                        anilist_id=a.id,
                        season=season,
                        year=year,
                        title=a.title,
                        genres=a.genres,
                        tags=a.tags,
                        synopsis=a.synopsis,
                        score=a.score,
                        episodes=a.episodes,
                        status=a.status,
                        cover_image=a.cover_image,
                    )
                    await self._session.merge(row)
                await self._session.commit()
            except SQLAlchemyError as e:
                raise DatabaseError(f"DB unavailable: {e}") from e

    async def get_search_cache(self, cache_key: str) -> list[AnimeEntry] | None:
        async with self._lock:
            try:
                result = await self._session.execute(
                    select(SearchCacheORM).where(SearchCacheORM.cache_key == cache_key)
                )
            except SQLAlchemyError as e:
                raise DatabaseError(f"DB unavailable: {e}") from e
            row = result.scalar_one_or_none()
        if row is None:
            return None
        if datetime.utcnow() - row.fetched_at > _SEARCH_TTL:
            return None
        return [AnimeEntry.model_validate(item) for item in row.results]

    async def store_search_cache(
        self, cache_key: str, anime: list[AnimeEntry]
    ) -> None:
        async with self._lock:
            try:
                row = SearchCacheORM(
                    cache_key=cache_key,
                    results=[a.model_dump() for a in anime],
                    fetched_at=datetime.utcnow(),
                )
                await self._session.merge(row)
                await self._session.commit()
            except SQLAlchemyError as e:
                raise DatabaseError(f"DB unavailable: {e}") from e


def _seasonal_to_domain(row: SeasonalAnimeORM) -> AnimeEntry:
    return AnimeEntry(
        id=row.anilist_id,
        title=row.title,
        genres=list(row.genres),
        tags=list(row.tags),
        synopsis=row.synopsis,
        score=row.score,
        episodes=row.episodes,
        status=row.status,
        cover_image=row.cover_image,
    )
