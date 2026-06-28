import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.application.recommend_service import RecommendService, get_recommend_service
from src.domain.models import RecommendationRequest, RecommendationResponse

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.post("/", response_model=RecommendationResponse)
async def recommend(
    request: RecommendationRequest,
    service: RecommendService = Depends(get_recommend_service),
) -> RecommendationResponse:
    return await service.recommend(request)


@router.post("/stream")
async def recommend_stream(
    request: RecommendationRequest,
    service: RecommendService = Depends(get_recommend_service),
) -> StreamingResponse:
    async def event_source() -> AsyncIterator[str]:
        async for event in service.recommend_stream(request):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
