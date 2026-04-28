import httpx

from src.domain.exceptions import AniListError
from src.domain.models import AnimeEntry

_SEASONAL_QUERY = """
query ($season: MediaSeason, $year: Int, $page: Int) {
  Page(page: $page, perPage: 50) {
    media(season: $season, seasonYear: $year, type: ANIME, sort: POPULARITY_DESC) {
      id
      title { english romaji }
      genres
      description(asHtml: false)
      averageScore
      episodes
      status
    }
  }
}
"""

_SEARCH_QUERY = """
query ($genres: [String], $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(genre_in: $genres, type: ANIME, sort: SCORE_DESC, isAdult: false) {
      id
      title { english romaji }
      genres
      description(asHtml: false)
      averageScore
      episodes
      status
    }
  }
}
"""


class AniListClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    async def search_all(
        self,
        genres: list[str] | None = None,
        per_page: int = 50,
    ) -> list[AnimeEntry]:
        variables: dict[str, object] = {"page": 1, "perPage": per_page}
        if genres:
            variables["genres"] = genres
        return await self._execute(_SEARCH_QUERY, variables)

    async def get_seasonal(self, season: str, year: int) -> list[AnimeEntry]:
        return await self._execute(
            _SEASONAL_QUERY,
            {"season": season, "year": year, "page": 1},
        )

    async def _execute(
        self, query: str, variables: dict[str, object]
    ) -> list[AnimeEntry]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self._base_url,
                    json={"query": query, "variables": variables},
                )
            except httpx.RequestError as e:
                raise AniListError(f"AniList unreachable: {e}") from e
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise AniListError(
                    f"AniList returned {e.response.status_code}: {e.response.text}"
                ) from e
            try:
                data = response.json()
                media_list: list[dict[str, object]] = data["data"]["Page"]["media"]
            except (KeyError, ValueError) as e:
                raise AniListError(f"Unexpected AniList response shape: {e}") from e
            return [_parse_entry(m) for m in media_list]


def _parse_entry(raw: dict[str, object]) -> AnimeEntry:
    title_obj = raw.get("title") or {}
    assert isinstance(title_obj, dict)
    title = str(title_obj.get("english") or title_obj.get("romaji") or "Unknown")
    score_raw = raw.get("averageScore")
    episodes_raw = raw.get("episodes")
    return AnimeEntry(
        id=int(str(raw["id"])),
        title=title,
        genres=[str(g) for g in (raw.get("genres") or [])],
        synopsis=str(raw.get("description") or ""),
        score=float(str(score_raw)) / 10.0 if score_raw else None,
        episodes=int(str(episodes_raw)) if episodes_raw else None,
        status=str(raw.get("status") or ""),
    )
