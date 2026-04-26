from fastapi import Depends
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ..agent.runner import run_recommendation_agent
from ..config import settings
from ..domain.models import RecommendationRequest, RecommendationResponse
from ..infrastructure.anilist_client import AniListClient
from ..infrastructure.anime_repository import AnimeRepository
from ..infrastructure.catalog_service import CatalogService
from ..infrastructure.database import get_db_session


class RecommendService:
    def __init__(self, client: AsyncOpenAI, catalog: CatalogService) -> None:
        self._client = client
        self._catalog = catalog

    async def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        return await run_recommendation_agent(self._client, self._catalog, request)


def get_recommend_service(
    session: AsyncSession = Depends(get_db_session),
) -> RecommendService:
    return RecommendService(
        client=AsyncOpenAI(
            api_key=settings.groq_api_key, base_url=settings.groq_base_url
        ),
        catalog=CatalogService(
            anilist=AniListClient(base_url=settings.anilist_api_url),
            repo=AnimeRepository(session),
        ),
    )
