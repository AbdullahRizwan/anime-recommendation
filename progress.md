# Progress

## Current focus: agent toolset + SSE progress rework

A single body of work (currently **uncommitted**, on top of commit `965c43a`) addressing
the three open architectural issues. All three are **resolved**.

### Status: ✅ Complete & verified (not yet committed)

| Check | Result |
|-------|--------|
| API tests (`pytest`) | ✅ 24 passed |
| TODO / FIXME / WIP markers in changed files | ✅ None |
| Web source lint | ✅ Passes (only an unrelated `.impeccable` cache file flags) |

---

## What changed

### 1. Real SSE progress (was: cosmetic timers)
- Backend streams from `POST /api/v1/recommend/stream` (`apps/api/src/routers/recommend.py`).
- Tools emit `started`/`finished` events via `Deps.emit` (`apps/api/src/agent/tools.py`).
- `run_recommendation_agent_stream` races a progress queue against the agent task,
  with a 120s timeout (`apps/api/src/agent/runner.py`).
- Frontend reads the stream through the Next route handler
  `apps/web/app/api/recommend/stream/route.ts` and renders real per-tool progress in
  `PreferencesForm.tsx`. Fake `setTimeout` step timers removed.
- `apps/web/app/actions.ts` deleted (server action replaced by the API route).

### 2. Toolset collapsed 4 → 1 (was: fragmented, stateful tools)
- `get_seasonal_anime`, `search_all_anime`, `filter_anime`, `rank_anime` removed.
- Replaced by one self-contained `search_catalog` (fetch + filter + sort + full details).
- Pure, side-effect-free `_filter_entries` helper.
- Final output enriched authoritatively by id in `runner.py::_enrich`
  (titles, scores, cover images taken from the catalog, never model-transcribed).

### 3. Agent rigidity (was: fixed fetch→filter→rank recipe)
- System prompt in `agent.py` rewritten to be principle-based: encourages multiple
  varied searches, weighting user notes over genre labels, ranking as the agent's own
  judgment.

### Supporting changes
- New migration `0004_add_tags_to_anime_cache.py` (+ `orm_models.py` tags column).
- New `apps/api/tests/test_repository.py`; expanded `apps/api/tests/test_tools.py`.
- `_SYNOPSIS_LIMIT` bumped 300 → 400.

---

## Remaining / loose ends
- [ ] **Commit the work** (the only thing genuinely outstanding) — in logical chunks.
- [ ] Non-blocking: `datetime.utcnow()` `DeprecationWarning` in
  `apps/api/src/infrastructure/anime_repository.py:89` — switch to
  `datetime.now(datetime.UTC)`.
