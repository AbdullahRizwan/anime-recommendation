from openai import AsyncOpenAI

from ..agent.runner import run_recommendation_agent
from ..config import settings
from ..domain.models import RecommendationRequest, RecommendationResponse
from ..infrastructure.anilist_client import AniListClient


class RecommendService:
    def __init__(self, client: AsyncOpenAI, anilist: AniListClient) -> None:
        self._client = client
        self._anilist = anilist

    async def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        return await run_recommendation_agent(self._client, self._anilist, request)


def get_recommend_service() -> RecommendService:
    return RecommendService(
        client=AsyncOpenAI(
            api_key=settings.groq_api_key, base_url=settings.groq_base_url
        ),
        anilist=AniListClient(base_url=settings.anilist_api_url),
    )
