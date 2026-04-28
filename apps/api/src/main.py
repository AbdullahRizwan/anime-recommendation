import logfire
import openai
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import settings
from .domain.exceptions import AgentError, AniListError
from .presentation.routers import recommend

logfire.configure(
    token=settings.logfire_token or None,
    send_to_logfire="if-token-present",
)

app = FastAPI(title="Anime Triage API", version="0.1.0")

logfire.instrument_fastapi(app)

app.include_router(recommend.router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(AniListError)
async def anilist_error_handler(request: Request, exc: AniListError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"error": "anime_data_unavailable", "detail": str(exc)},
    )


@app.exception_handler(AgentError)
async def agent_error_handler(request: Request, exc: AgentError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"error": "agent_failed", "detail": str(exc)},
    )


@app.exception_handler(openai.RateLimitError)
async def rate_limit_handler(
    request: Request, exc: openai.RateLimitError
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limited", "detail": "Rate limit hit, try again later."},
    )


@app.exception_handler(openai.APIError)
async def openai_error_handler(request: Request, exc: openai.APIError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"error": "llm_unavailable", "detail": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "An unexpected error occurred."},
    )
