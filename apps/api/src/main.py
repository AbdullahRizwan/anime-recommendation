from fastapi import FastAPI

from .presentation.routers import recommend

app = FastAPI(title="Anime Triage API", version="0.1.0")

app.include_router(recommend.router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
