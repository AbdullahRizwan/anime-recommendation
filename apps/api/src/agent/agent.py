from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from ..config import settings
from ..domain.models import RecommendationResponse
from .tools import Deps, filter_anime, get_seasonal_anime, rank_anime, search_all_anime

agent: Agent[Deps, RecommendationResponse] = Agent(
    model=OpenAIChatModel(
        "gpt-4o-mini", provider=OpenAIProvider(api_key=settings.openai_api_key)
    ),
    output_type=RecommendationResponse,
    deps_type=Deps,
    tools=[get_seasonal_anime, search_all_anime, filter_anime, rank_anime],
)


@agent.system_prompt
def _build_system_prompt(ctx: RunContext[Deps]) -> str:
    prefs = ctx.deps.request.preferences
    top_n = ctx.deps.request.top_n
    return (
        "You are an anime triage agent. Use the available tools to find and rank anime.\n\n"
        "Tool selection rules:\n"
        "- Use search_all_anime when the user has genre or theme preferences — it searches "
        "AniList's full catalog (all years, sorted by score), so classic and older series are included.\n"
        "- Use get_seasonal_anime only when the user explicitly asks for what is currently airing "
        f"this season ({ctx.deps.season} {ctx.deps.year}).\n"
        "- After fetching, call filter_anime to narrow results. Pass synopsis_keywords (e.g. "
        "'horror', 'gore', 'psychological') alongside genre filters — genre tags alone miss "
        "many thematically relevant shows.\n"
        "- Finally call rank_anime with your top picks and return the ranked list.\n\n"
        f"User likes: {', '.join(prefs.liked_genres) or 'no preference'}\n"
        f"User dislikes: {', '.join(prefs.disliked_genres) or 'none'}\n"
        f"Notes: {prefs.notes or 'none'}\n"
        f"Return top {top_n} recommendations."
    )
