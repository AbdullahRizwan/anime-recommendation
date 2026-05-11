import html
import re

import httpx

from src.domain.exceptions import AniListError
from src.domain.models import AnimeEntry

# AniList's fixed genre list — everything else is a tag and must use tag_in.
_ANILIST_GENRES = {
    "action", "adventure", "comedy", "drama", "ecchi", "fantasy", "hentai",
    "horror", "mahou shoujo", "mecha", "music", "mystery", "psychological",
    "romance", "sci-fi", "slice of life", "sports", "supernatural", "thriller",
}

# Only include tags with rank >= this threshold to avoid low-confidence noise.
_TAG_RANK_MIN = 60

_MEDIA_FIELDS = """
      id
      title { english romaji }
      genres
      tags { name rank }
      description(asHtml: false)
      averageScore
      episodes
      status
      coverImage { large }
"""

_SEASONAL_QUERY = """
query ($season: MediaSeason, $year: Int, $isAdult: Boolean, $page: Int) {
  Page(page: $page, perPage: 50) {
    media(season: $season, seasonYear: $year, type: ANIME, sort: POPULARITY_DESC, isAdult: $isAdult) {
""" + _MEDIA_FIELDS + """
    }
  }
}
"""

_SEARCH_QUERY = """
query ($genres: [String], $tags: [String], $isAdult: Boolean, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(genre_in: $genres, tag_in: $tags, type: ANIME, sort: SCORE_DESC, isAdult: $isAdult) {
""" + _MEDIA_FIELDS + """
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
        allow_explicit: bool = False,
    ) -> list[AnimeEntry]:
        genre_list: list[str] = []
        tag_list: list[str] = []
        for g in (genres or []):
            if g.lower() in _ANILIST_GENRES:
                genre_list.append(g)
            else:
                tag_list.append(g)
        variables: dict[str, object] = {"page": 1, "perPage": per_page}
        if genre_list:
            variables["genres"] = genre_list
        if tag_list:
            variables["tags"] = tag_list
        if not allow_explicit:
            variables["isAdult"] = False
        return await self._execute(_SEARCH_QUERY, variables)

    async def get_seasonal(
        self,
        season: str,
        year: int,
        allow_explicit: bool = False,
    ) -> list[AnimeEntry]:
        variables: dict[str, object] = {"season": season, "year": year, "page": 1}
        if not allow_explicit:
            variables["isAdult"] = False
        return await self._execute(_SEASONAL_QUERY, variables)

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


def _clean_synopsis(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return " ".join(text.split())


def _parse_entry(raw: dict[str, object]) -> AnimeEntry:
    title_obj = raw.get("title") or {}
    assert isinstance(title_obj, dict)
    title = str(title_obj.get("english") or title_obj.get("romaji") or "Unknown")
    score_raw = raw.get("averageScore")
    episodes_raw = raw.get("episodes")
    cover_obj = raw.get("coverImage") or {}
    assert isinstance(cover_obj, dict)
    cover_image = str(cover_obj["large"]) if cover_obj.get("large") else None
    raw_tags = raw.get("tags") or []
    assert isinstance(raw_tags, list)
    tags = [
        str(t["name"])
        for t in raw_tags
        if isinstance(t, dict) and t.get("name") and int(t.get("rank", 0)) >= _TAG_RANK_MIN
    ]
    return AnimeEntry(
        id=int(str(raw["id"])),
        title=title,
        genres=[str(g) for g in (raw.get("genres") or [])],
        tags=tags,
        synopsis=_clean_synopsis(str(raw.get("description") or "")),
        score=float(str(score_raw)) / 10.0 if score_raw else None,
        episodes=int(str(episodes_raw)) if episodes_raw else None,
        status=str(raw.get("status") or ""),
        cover_image=cover_image,
    )
