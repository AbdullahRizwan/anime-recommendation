import json
from unittest.mock import MagicMock

import pytest

from src.agent.tools import filter_anime, rank_anime
from src.domain.models import AnimeEntry


def _entry(**kwargs) -> AnimeEntry:
    defaults: dict = {
        "id": 1,
        "title": "Test Anime",
        "genres": [],
        "tags": [],
        "synopsis": "",
        "score": 7.5,
        "episodes": 12,
        "status": "FINISHED",
        "cover_image": None,
    }
    return AnimeEntry(**{**defaults, **kwargs})


def _ctx(store: dict) -> MagicMock:
    ctx = MagicMock()
    ctx.deps.store = store
    return ctx


# ── filter_anime ──────────────────────────────────────────────────────────────

class TestFilterByGenreTag:
    async def test_passes_on_genre_match(self) -> None:
        entry = _entry(id=1, genres=["Horror", "Drama"])
        result = json.loads(await filter_anime(_ctx({1: entry}), [1], include_genres=["Horror"]))
        assert len(result) == 1

    async def test_passes_on_tag_match(self) -> None:
        """Harem is an AniList tag, not a genre — should still pass."""
        entry = _entry(id=1, genres=["Comedy"], tags=["Harem"])
        result = json.loads(await filter_anime(_ctx({1: entry}), [1], include_genres=["Harem"]))
        assert len(result) == 1

    async def test_passes_on_synopsis_keyword_fallback(self) -> None:
        """No genre/tag match, but synopsis contains a mapped keyword."""
        entry = _entry(id=1, genres=["Drama"], synopsis="A haunted house full of dread.")
        result = json.loads(await filter_anime(_ctx({1: entry}), [1], include_genres=["Horror"]))
        assert len(result) == 1

    async def test_filters_out_unrelated(self) -> None:
        entry = _entry(id=1, genres=["Action"], tags=[], synopsis="Two warriors clash.")
        result = json.loads(await filter_anime(_ctx({1: entry}), [1], include_genres=["Harem"]))
        assert len(result) == 0

    async def test_skips_missing_ids(self) -> None:
        result = json.loads(await filter_anime(_ctx({}), [99], include_genres=["Action"]))
        assert result == []


class TestFilterExcludeGenres:
    async def test_excludes_by_genre(self) -> None:
        entry = _entry(id=1, genres=["Ecchi", "Action"])
        result = json.loads(await filter_anime(_ctx({1: entry}), [1], exclude_genres=["Ecchi"]))
        assert len(result) == 0

    async def test_excludes_by_tag(self) -> None:
        entry = _entry(id=1, genres=["Action"], tags=["Gore"])
        result = json.loads(await filter_anime(_ctx({1: entry}), [1], exclude_genres=["Gore"]))
        assert len(result) == 0

    async def test_keeps_when_no_excluded_match(self) -> None:
        entry = _entry(id=1, genres=["Action"])
        result = json.loads(await filter_anime(_ctx({1: entry}), [1], exclude_genres=["Horror"]))
        assert len(result) == 1


class TestFilterEpisodes:
    async def test_filters_over_limit(self) -> None:
        entry = _entry(id=1, genres=["Action"], episodes=24)
        result = json.loads(await filter_anime(_ctx({1: entry}), [1], max_episodes=12))
        assert len(result) == 0

    async def test_passes_within_limit(self) -> None:
        entry = _entry(id=1, genres=["Action"], episodes=12)
        result = json.loads(await filter_anime(_ctx({1: entry}), [1], max_episodes=12))
        assert len(result) == 1

    async def test_passes_null_episodes(self) -> None:
        entry = _entry(id=1, genres=["Action"], episodes=None)
        result = json.loads(await filter_anime(_ctx({1: entry}), [1], max_episodes=12))
        assert len(result) == 1


class TestFilterExplicitKeywords:
    async def test_explicit_keywords_and_with_genre(self) -> None:
        entry = _entry(id=1, genres=["Horror"], synopsis="A horror romance.")
        result = json.loads(
            await filter_anime(_ctx({1: entry}), [1], include_genres=["Horror"], synopsis_keywords=["romance"])
        )
        assert len(result) == 1

    async def test_explicit_keywords_fails_when_absent(self) -> None:
        entry = _entry(id=1, genres=["Horror"], synopsis="Pure terror.")
        result = json.loads(
            await filter_anime(_ctx({1: entry}), [1], include_genres=["Horror"], synopsis_keywords=["romance"])
        )
        assert len(result) == 0


# ── rank_anime ────────────────────────────────────────────────────────────────

class TestRankAnime:
    async def test_returns_top_n(self) -> None:
        store = {i: _entry(id=i) for i in range(1, 6)}
        result = json.loads(await rank_anime(_ctx(store), list(store.keys()), top_n=3))
        assert len(result) == 3

    async def test_skips_missing_ids(self) -> None:
        store = {1: _entry(id=1)}
        result = json.loads(await rank_anime(_ctx(store), [1, 99, 100], top_n=5))
        assert len(result) == 1


# ── AniList genre/tag routing ─────────────────────────────────────────────────

class TestAniListGenreSet:
    def test_known_genres_present(self) -> None:
        from src.infrastructure.anilist_client import _ANILIST_GENRES
        assert "horror" in _ANILIST_GENRES
        assert "romance" in _ANILIST_GENRES
        assert "sci-fi" in _ANILIST_GENRES

    def test_themes_absent(self) -> None:
        from src.infrastructure.anilist_client import _ANILIST_GENRES
        assert "harem" not in _ANILIST_GENRES
        assert "isekai" not in _ANILIST_GENRES
        assert "school" not in _ANILIST_GENRES
