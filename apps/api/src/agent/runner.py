from datetime import date

from src.domain.exceptions import AgentError
from src.domain.models import RecommendationRequest, RecommendationResponse
from src.infrastructure.catalog_service import CatalogService
from src.agent.agent import agent
from src.agent.tools import Deps


def _resolve_season(request: RecommendationRequest) -> tuple[str, int]:
    if request.season and request.year:
        return request.season, request.year
    today = date.today()
    month = today.month
    season = (
        "WINTER" if month <= 3 else
        "SPRING" if month <= 6 else
        "SUMMER" if month <= 9 else
        "FALL"
    )
    return season, today.year


async def run_recommendation_agent(
    catalog: CatalogService,
    request: RecommendationRequest,
) -> RecommendationResponse:
    season, year = _resolve_season(request)
    deps = Deps(catalog=catalog, request=request, season=season, year=year)
    if request.season and request.year:
        prompt = f"Recommend the top {request.top_n} anime currently airing in {season} {year}."
    else:
        prompt = f"Recommend the top {request.top_n} anime based on the user's preferences."
    try:
        result = await agent.run(prompt, deps=deps)
    except Exception as e:
        raise AgentError(str(e)) from e
    return result.output
