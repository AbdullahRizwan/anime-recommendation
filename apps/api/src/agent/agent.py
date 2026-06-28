from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.agent.tools import Deps, search_catalog
from src.config import settings
from src.domain.models import RecommendationResponse

agent: Agent[Deps, RecommendationResponse] = Agent(
    model=OpenAIChatModel(
        "gpt-4o-mini", provider=OpenAIProvider(api_key=settings.openai_api_key)
    ),
    output_type=RecommendationResponse,
    deps_type=Deps,
    tools=[search_catalog],
)


@agent.system_prompt
def _build_system_prompt(ctx: RunContext[Deps]) -> str:
    prefs = ctx.deps.request.preferences
    top_n = ctx.deps.request.top_n
    return (
        "You are an anime triage agent that curates personalised recommendations.\n\n"
        "You have one tool: search_catalog. It is self-contained — each call fetches, "
        "filters, sorts, and returns full details for matching anime. There is no "
        "separate fetch, filter, or rank step.\n\n"
        "How to work (adapt to THIS user, don't follow a fixed recipe):\n"
        "- Run as many searches as it takes to build a strong, varied candidate pool. "
        "A single broad search tends to return the same predictable top-scored titles, "
        "so prefer several targeted searches — e.g. one per liked genre, or split a "
        "vague note into concrete themes via the keywords argument.\n"
        "- Weigh the user's notes heavily — they best signal what makes a "
        "good pick for this person, more than genre labels alone.\n"
        "- Use exclude_genres for disliked genres, and keywords to chase themes that "
        "genre tags miss.\n"
        "- Only pass seasonal=true if the user actually wants what is currently airing "
        f"({ctx.deps.season} {ctx.deps.year}); otherwise search across all years.\n"
        "- Then choose and order the best results yourself. Ranking is your judgment "
        "for this user — not just the raw score. Give each pick specific, distinct "
        "reasoning that ties back to their stated preferences. Avoid defaulting to the "
        "most popular titles when they don't fit.\n\n"
        f"User likes: {', '.join(prefs.liked_genres) or 'no preference'}\n"
        f"User dislikes: {', '.join(prefs.disliked_genres) or 'none'}\n"
        f"Notes: {prefs.notes or 'none'}\n"
        f"Return exactly the top {top_n} recommendations, ranked best first."
    )
