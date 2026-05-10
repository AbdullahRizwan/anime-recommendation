from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    liked_genres: list[str] = Field(default_factory=list)
    disliked_genres: list[str] = Field(default_factory=list)
    notes: str = ""


class RankedAnime(BaseModel):
    id: int
    title: str
    rank: int
    score: float
    reasoning: str
    cover_image: str | None = None


class RecommendationRequest(BaseModel):
    preferences: UserPreferences
    season: str | None = None
    year: int | None = None
    top_n: int = Field(default=10, ge=1, le=50)


class RecommendationResponse(BaseModel):
    recommendations: list[RankedAnime]
    season: str
    year: int
    reasoning_summary: str
