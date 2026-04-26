from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.models import AnimeEntry
from .orm_models import SeasonalAnimeORM


class AnimeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_seasonal(
        self, season: str, year: int
    ) -> list[AnimeEntry] | None:
        result = await self._session.execute(
            select(SeasonalAnimeORM).where(
                SeasonalAnimeORM.season == season,
                SeasonalAnimeORM.year == year,
            )
        )
        rows = result.scalars().all()
        if not rows:
            return None
        return [_to_domain(row) for row in rows]

    async def store_seasonal(
        self, season: str, year: int, anime: list[AnimeEntry]
    ) -> None:
        for a in anime:
            row = SeasonalAnimeORM(
                anilist_id=a.id,
                season=season,
                year=year,
                title=a.title,
                genres=a.genres,
                synopsis=a.synopsis,
                score=a.score,
                episodes=a.episodes,
                status=a.status,
            )
            await self._session.merge(row)
        await self._session.commit()


def _to_domain(row: SeasonalAnimeORM) -> AnimeEntry:
    return AnimeEntry(
        id=row.anilist_id,
        title=row.title,
        genres=list(row.genres),
        synopsis=row.synopsis,
        score=row.score,
        episodes=row.episodes,
        status=row.status,
    )
