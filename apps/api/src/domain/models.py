from pydantic import BaseModel, Field


class AnimeEntry(BaseModel):
    id: int
    title: str
    genres: list[str]
    tags: list[str] = []
    synopsis: str
    score: float | None
    episodes: int | None
    status: str
    cover_image: str | None = None


class UserPreferences(BaseModel):
    liked_genres: list[str] = Field(default_factory=list)
    disliked_genres: list[str] = Field(default_factory=list)
    preferred_episode_count: int | None = None
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
    season: str | None = None  # e.g. "WINTER", "SPRING", "SUMMER", "FALL"
    year: int | None = None
    top_n: int = Field(default=10, ge=1, le=50)


class RecommendationResponse(BaseModel):
    recommendations: list[RankedAnime]
    season: str
    year: int
    reasoning_summary: str
