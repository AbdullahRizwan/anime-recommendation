from fastapi import APIRouter, Depends

from ...application.recommend_service import RecommendService, get_recommend_service
from ...domain.models import RecommendationRequest, RecommendationResponse

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.post("/", response_model=RecommendationResponse)
async def recommend(
    request: RecommendationRequest,
    service: RecommendService = Depends(get_recommend_service),
) -> RecommendationResponse:
    return await service.recommend(request)
