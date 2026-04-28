from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.runner import run_recommendation_agent
from src.config import settings
from src.domain.models import RecommendationRequest, RecommendationResponse
from src.infrastructure.anilist_client import AniListClient
from src.infrastructure.anime_repository import AnimeRepository
from src.infrastructure.catalog_service import CatalogService
from src.infrastructure.database import get_db_session


class RecommendService:
    def __init__(self, catalog: CatalogService) -> None:
        self._catalog = catalog

    async def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        return await run_recommendation_agent(self._catalog, request)


def get_recommend_service(
    session: AsyncSession = Depends(get_db_session),
) -> RecommendService:
    return RecommendService(
        catalog=CatalogService(
            anilist=AniListClient(base_url=settings.anilist_api_url),
            repo=AnimeRepository(session),
        ),
    )
