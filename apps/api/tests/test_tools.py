import json
from unittest.mock import AsyncMock, MagicMock

from src.agent.tools import Deps, _filter_entries, search_catalog
from src.domain.models import AnimeEntry, RecommendationRequest, UserPreferences


def _entry(**kwargs: object) -> AnimeEntry:
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


def _deps(catalog: MagicMock, allow_explicit: bool = False) -> Deps:
    request = RecommendationRequest(
        preferences=UserPreferences(allow_explicit=allow_explicit)
    )
    return Deps(catalog=catalog, request=request, season="SPRING", year=2026)


def _ctx(deps: Deps) -> MagicMock:
    ctx = MagicMock()
    ctx.deps = deps
    return ctx


# ── _filter_entries (pure) ────────────────────────────────────────────────────

class TestFilterByGenreTag:
    def test_passes_on_genre_match(self) -> None:
        entry = _entry(id=1, genres=["Horror", "Drama"])
        assert len(_filter_entries([entry], include_genres=["Horror"])) == 1

    def test_passes_on_tag_match(self) -> None:
        """Harem is an AniList tag, not a genre — should still pass."""
        entry = _entry(id=1, genres=["Comedy"], tags=["Harem"])
        assert len(_filter_entries([entry], include_genres=["Harem"])) == 1

    def test_passes_on_synopsis_keyword_fallback(self) -> None:
        """No genre/tag match, but synopsis contains a mapped keyword."""
        entry = _entry(id=1, genres=["Drama"], synopsis="A haunted house of dread.")
        assert len(_filter_entries([entry], include_genres=["Horror"])) == 1

    def test_filters_out_unrelated(self) -> None:
        entry = _entry(id=1, genres=["Action"], tags=[], synopsis="Two warriors clash.")
        assert len(_filter_entries([entry], include_genres=["Harem"])) == 0


class TestFilterExcludeGenres:
    def test_excludes_by_genre(self) -> None:
        entry = _entry(id=1, genres=["Ecchi", "Action"])
        assert len(_filter_entries([entry], exclude_genres=["Ecchi"])) == 0

    def test_excludes_by_tag(self) -> None:
        entry = _entry(id=1, genres=["Action"], tags=["Gore"])
        assert len(_filter_entries([entry], exclude_genres=["Gore"])) == 0

    def test_keeps_when_no_excluded_match(self) -> None:
        entry = _entry(id=1, genres=["Action"])
        assert len(_filter_entries([entry], exclude_genres=["Horror"])) == 1


class TestFilterEpisodes:
    def test_filters_over_limit(self) -> None:
        entry = _entry(id=1, genres=["Action"], episodes=24)
        assert len(_filter_entries([entry], max_episodes=12)) == 0

    def test_passes_within_limit(self) -> None:
        entry = _entry(id=1, genres=["Action"], episodes=12)
        assert len(_filter_entries([entry], max_episodes=12)) == 1

    def test_passes_null_episodes(self) -> None:
        entry = _entry(id=1, genres=["Action"], episodes=None)
        assert len(_filter_entries([entry], max_episodes=12)) == 1


class TestFilterScore:
    def test_filters_below_min_score(self) -> None:
        entry = _entry(id=1, genres=["Action"], score=6.0)
        assert len(_filter_entries([entry], min_score=7.0)) == 0

    def test_passes_at_or_above_min_score(self) -> None:
        entry = _entry(id=1, genres=["Action"], score=8.0)
        assert len(_filter_entries([entry], min_score=7.0)) == 1

    def test_passes_null_score(self) -> None:
        entry = _entry(id=1, genres=["Action"], score=None)
        assert len(_filter_entries([entry], min_score=7.0)) == 1


class TestFilterKeywords:
    def test_keywords_and_with_genre(self) -> None:
        entry = _entry(id=1, genres=["Horror"], synopsis="A horror romance.")
        result = _filter_entries(
            [entry], include_genres=["Horror"], keywords=["romance"]
        )
        assert len(result) == 1

    def test_keywords_fails_when_absent(self) -> None:
        entry = _entry(id=1, genres=["Horror"], synopsis="Pure terror.")
        result = _filter_entries(
            [entry], include_genres=["Horror"], keywords=["romance"]
        )
        assert len(result) == 0


# ── search_catalog (standalone tool) ──────────────────────────────────────────

class TestSearchCatalog:
    async def test_all_time_search_fetches_filters_and_sorts(self) -> None:
        catalog = MagicMock()
        catalog.search_all = AsyncMock(
            return_value=[
                _entry(id=1, genres=["Action"], score=6.0),
                _entry(id=2, genres=["Action"], score=9.0),
                _entry(id=3, genres=["Romance"], score=8.0),
            ]
        )
        deps = _deps(catalog)
        result = json.loads(
            await search_catalog(_ctx(deps), genres=["Action"], limit=10)
        )
        # Romance dropped by include filter; remaining sorted by score desc.
        assert [r["id"] for r in result] == [2, 1]
        catalog.search_all.assert_awaited_once()

    async def test_seasonal_uses_get_seasonal(self) -> None:
        catalog = MagicMock()
        catalog.get_seasonal = AsyncMock(
            return_value=[_entry(id=1, genres=["Action"], score=7.0)]
        )
        catalog.search_all = AsyncMock(return_value=[])
        deps = _deps(catalog)
        result = json.loads(await search_catalog(_ctx(deps), seasonal=True))
        assert len(result) == 1
        catalog.get_seasonal.assert_awaited_once_with(
            "SPRING", 2026, allow_explicit=False
        )
        catalog.search_all.assert_not_awaited()

    async def test_limit_caps_results(self) -> None:
        catalog = MagicMock()
        catalog.search_all = AsyncMock(
            return_value=[
                _entry(id=i, genres=["Action"], score=float(i)) for i in range(1, 11)
            ]
        )
        deps = _deps(catalog)
        result = json.loads(
            await search_catalog(_ctx(deps), genres=["Action"], limit=3)
        )
        assert len(result) == 3
        # Highest scores first.
        assert [r["id"] for r in result] == [10, 9, 8]

    async def test_populates_store_for_enrichment(self) -> None:
        catalog = MagicMock()
        catalog.search_all = AsyncMock(
            return_value=[_entry(id=42, genres=["Action"], title="Real Title")]
        )
        deps = _deps(catalog)
        await search_catalog(_ctx(deps), genres=["Action"])
        assert 42 in deps.store
        assert deps.store[42].title == "Real Title"

    async def test_emits_progress_events(self) -> None:
        import asyncio

        catalog = MagicMock()
        catalog.search_all = AsyncMock(
            return_value=[_entry(id=1, genres=["Action"])]
        )
        deps = _deps(catalog)
        deps.events = asyncio.Queue()
        await search_catalog(_ctx(deps), genres=["Action"])
        events = []
        while not deps.events.empty():
            events.append(deps.events.get_nowait())
        statuses = [e["status"] for e in events]
        assert statuses == ["started", "finished"]
        assert events[1]["count"] == 1


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
