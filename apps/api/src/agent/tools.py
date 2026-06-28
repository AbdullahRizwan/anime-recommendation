import asyncio
import json
from dataclasses import dataclass, field

from pydantic_ai import RunContext

from src.domain.models import AnimeEntry, RecommendationRequest
from src.infrastructure.catalog_service import CatalogService

_SYNOPSIS_LIMIT = 400

_GENRE_KEYWORDS: dict[str, list[str]] = {
    # ── Genres ────────────────────────────────────────────────────────────────
    "action": ["battle", "fight", "combat", "war", "clash", "fighting"],
    "adventure": ["adventure", "journey", "quest", "exploration", "expedition"],
    "avant garde": ["experimental", "surreal", "abstract", "unconventional", "avant-garde"],
    "boys love": ["boys love", "yaoi", "male romance", "two men in love", "gay romance"],
    "comedy": ["comedy", "hilarious", "funny", "humor", "gag", "laugh"],
    "drama": ["drama", "emotional", "tragedy", "grief", "loss", "heartbreak"],
    "fantasy": ["magic", "wizard", "dragon", "elf", "sorcery", "mythical", "enchanted"],
    "girls love": ["girls love", "yuri", "female romance", "two women in love", "lesbian romance"],
    "gourmet": ["food", "cooking", "cuisine", "chef", "restaurant", "culinary", "recipe"],
    "horror": ["horror", "terror", "haunted", "monster", "dread", "fear", "cursed", "frightening"],
    "mystery": ["mystery", "detective", "investigation", "clue", "murder", "crime", "whodunit"],
    "romance": ["romance", "love", "relationship", "confession", "heartbreak", "falling in love"],
    "sci-fi": ["science fiction", "robot", "alien", "futuristic", "cyberpunk", "artificial intelligence"],
    "slice of life": ["daily life", "everyday", "mundane", "ordinary life", "coming of age"],
    "sports": ["sports", "tournament", "competition", "athlete", "training", "match"],
    "supernatural": ["spirit", "ghost", "demon", "curse", "paranormal", "occult", "otherworldly"],
    "suspense": ["suspense", "tension", "conspiracy", "danger", "tense", "thriller"],
    # ── Explicit genres ───────────────────────────────────────────────────────
    "ecchi": ["fanservice", "revealing", "suggestive", "lewd", "sexual humor"],
    "erotica": ["erotic", "adult content", "explicit", "sexual content"],
    "hentai": ["explicit sexual", "adult anime", "pornographic"],
    # ── Themes ────────────────────────────────────────────────────────────────
    "adult cast": ["adult protagonists", "working adults", "salaryman", "professionals"],
    "anthropomorphic": ["anthropomorphic", "animal characters", "talking animals", "humanoid animals"],
    "cgdct": ["cute girls", "moe", "all-female cast", "girls doing cute things"],
    "childcare": ["childcare", "babysitting", "raising children", "parenting", "daycare", "kindergarten"],
    "combat sports": ["boxing", "wrestling", "mma", "fighting competition", "combat sport"],
    "crossdressing": ["crossdressing", "cross-dress", "gender disguise", "dressed as opposite gender"],
    "delinquents": ["delinquent", "yankee", "juvenile", "school gang", "rebel", "troublemaker"],
    "detective": ["detective", "investigation", "case", "crime solving", "sleuth", "private investigator"],
    "educational": ["educational", "learn", "teach", "lesson", "knowledge"],
    "gag humor": ["gag", "slapstick", "absurd humor", "nonsensical", "ridiculous comedy"],
    "gore": ["gore", "graphic violence", "blood", "brutal", "gory", "gruesome", "dismember", "visceral"],
    "harem": ["harem", "Female harem", "Male Harem", "intercourse", "incest"],
    "high stakes game": ["death game", "life or death game", "deadly game", "gamble with life", "high-stakes"],
    "historical": ["historical", "feudal", "ancient", "medieval", "period drama", "edo", "meiji", "warring states"],
    "idols (female)": ["idol", "idol group", "pop star", "female idol", "idol training", "singing group"],
    "idols (male)": ["male idol", "boy band", "male singing group", "idol unit"],
    "isekai": ["another world", "reincarnated", "transported", "summoned", "parallel world", "different world"],
    "iyashikei": ["healing", "peaceful", "calming", "soothing", "relaxing", "wholesome", "gentle"],
    "love polygon": ["love triangle", "love polygon", "rivals in love", "competing for love"],
    "love status quo": ["unrequited love", "hidden feelings", "unspoken feelings", "won't confess"],
    "magical sex shift": ["gender swap", "gender bender", "body swap", "transformed into opposite gender"],
    "mahou shoujo": ["magical girl", "transformation", "fighting evil", "magical warrior", "magical powers"],
    "martial arts": ["martial arts", "kung fu", "karate", "judo", "kendo", "dojo", "fighting style", "sparring"],
    "mecha": ["giant robot", "mech suit", "humanoid machine", "robot battle", "cockpit", "pilot"],
    "medical": ["medical", "hospital", "doctor", "surgeon", "nurse", "disease", "diagnosis", "treatment"],
    "military": ["military", "soldiers", "army", "troops", "weapons", "combat unit", "squadron", "warfare"],
    "music": ["music", "band", "singer", "idol", "concert", "melody", "musician", "compose", "song"],
    "mythology": ["mythology", "myth", "god", "goddess", "legend", "deity", "divine", "ancient gods"],
    "organized crime": ["mafia", "yakuza", "gang", "criminal organization", "mob", "underworld"],
    "otaku culture": ["otaku", "anime fan", "manga", "figurine", "akihabara", "geek culture"],
    "parody": ["parody", "spoof", "satire", "genre parody", "comedic take"],
    "performing arts": ["theater", "acting", "stage", "musical", "drama club", "stage play"],
    "pets": ["pets", "dog", "cat", "animal companion", "caring for animals", "owner and pet"],
    "psychological": ["psychological", "trauma", "mental", "manipulation", "mind game", "mind-bending"],
    "racing": ["racing", "race", "car race", "speed", "driver", "circuit", "formula", "motorcycle race"],
    "reincarnation": ["reincarnation", "reborn", "past life", "previous life", "reincarnated as", "second life"],
    "reverse harem": ["reverse harem", "surrounded by men", "multiple male suitors", "female protagonist surrounded by men"],
    "samurai": ["samurai", "katana", "bushido", "shogunate", "ronin", "sword fight", "edo period"],
    "school": ["school", "high school", "student", "classroom", "academy", "campus", "club", "school life"],
    "showbiz": ["showbiz", "entertainment industry", "celebrity", "acting career", "talent agency", "audition"],
    "space": ["outer space", "spaceship", "galaxy", "planet", "astronaut", "intergalactic", "cosmos"],
    "strategy game": ["strategy", "chess", "shogi", "go", "tactics", "board game", "game of wit"],
    "super power": ["superpower", "special ability", "quirk", "superpower user", "superhuman"],
    "survival": ["survival", "stranded", "wilderness", "fight to survive", "deserted", "post-apocalyptic"],
    "team sports": ["basketball", "volleyball", "baseball", "soccer", "football team", "team competition"],
    "time travel": ["time travel", "time machine", "timeline", "time loop", "going back in time", "temporal"],
    "urban fantasy": ["urban fantasy", "modern magic", "magic in modern", "supernatural in city", "contemporary fantasy"],
    "vampire": ["vampire", "blood-sucking", "immortal", "fangs", "undead", "vampire hunter"],
    "video game": ["video game", "gamer", "virtual reality", "esports", "game tournament", "gaming"],
    "villainess": ["villainess", "otome game", "reincarnated as villain", "noble lady", "aristocrat antagonist"],
    "visual arts": ["art", "painting", "drawing", "illustration", "visual art", "artist", "gallery"],
    "workplace": ["workplace", "office", "job", "career", "coworkers", "profession", "work environment"],
    # ── Demographics ──────────────────────────────────────────────────────────
    "josei": ["mature romance", "adult women", "working women", "realistic relationship"],
    "kids": ["children", "kids", "family friendly", "young audience", "elementary school"],
    "seinen": ["mature themes", "dark themes", "adult men", "complex narrative"],
    "shoujo": ["teenage girl", "girl protagonist", "young woman", "first love"],
    "shounen": ["young boy", "coming of age", "power of friendship", "level up", "rivalry"],
}


@dataclass
class Deps:
    catalog: CatalogService
    request: RecommendationRequest
    season: str
    year: int
    # store is an authoritative record of every entry the agent has seen, keyed by
    # id. It is NOT used to chain tool calls together — each tool returns its own
    # full results — it exists only so the final output can be enriched with exact
    # titles, scores, and cover images (which the model must not transcribe by hand).
    store: dict[int, AnimeEntry] = field(default_factory=dict)
    # Optional progress channel. When set, tools push human-readable events that the
    # SSE endpoint streams to the UI so progress reflects real agent activity.
    events: "asyncio.Queue[dict[str, object]] | None" = None

    async def emit(self, event: dict[str, object]) -> None:
        if self.events is not None:
            await self.events.put(event)


def _filter_entries(
    entries: list[AnimeEntry],
    include_genres: list[str] | None = None,
    exclude_genres: list[str] | None = None,
    keywords: list[str] | None = None,
    max_episodes: int | None = None,
    min_score: float | None = None,
) -> list[AnimeEntry]:
    """Pure filter over a list of entries. Standalone and side-effect free.

    - include_genres: keep entries matching ANY genre/tag, OR whose synopsis contains
      a thematic keyword derived from that genre (so 'horror' also catches a synopsis
      about a haunted house even when 'Horror' isn't a listed genre).
    - exclude_genres: drop entries matching ANY genre/tag.
    - keywords: require at least one keyword to appear in the synopsis.
    - max_episodes / min_score: numeric gates (entries with null values pass).
    """
    include = {g.lower() for g in (include_genres or [])}
    exclude_set = {g.lower() for g in (exclude_genres or [])}
    explicit_kw = [k.lower() for k in (keywords or [])]

    derived_kw: list[str] = []
    for g in include:
        derived_kw.extend(_GENRE_KEYWORDS.get(g, []))

    results: list[AnimeEntry] = []
    for a in entries:
        categories = {g.lower() for g in a.genres} | {t.lower() for t in a.tags}
        if exclude_set and exclude_set & categories:
            continue
        if max_episodes and a.episodes and a.episodes > max_episodes:
            continue
        if min_score is not None and a.score is not None and a.score < min_score:
            continue
        synopsis_lower = a.synopsis.lower()
        if include:
            category_match = bool(include & categories)
            synopsis_match = any(k in synopsis_lower for k in derived_kw)
            if not category_match and not synopsis_match:
                continue
        if explicit_kw and not any(k in synopsis_lower for k in explicit_kw):
            continue
        results.append(a)
    return results


async def search_catalog(
    ctx: RunContext[Deps],
    genres: list[str] | None = None,
    exclude_genres: list[str] | None = None,
    keywords: list[str] | None = None,
    seasonal: bool = False,
    max_episodes: int | None = None,
    min_score: float | None = None,
    limit: int = 25,
) -> str:
    """Search the anime catalog and return COMPLETE details for every match.

    This is a single, standalone search: it fetches the catalog, applies all of the
    filters below, sorts by score, and returns full details (title, genres, tags,
    synopsis, score, episodes, status, cover image) — everything you need to reason
    about and rank results. You never need a separate fetch, filter, or rank step.

    Call it more than once with different criteria to assemble a varied candidate set
    (e.g. one search per liked genre, or a seasonal pass plus an all-time pass).

    Args:
        genres: include titles matching ANY of these genres/themes. Also expands to
            synopsis keywords, so thematically relevant shows are caught even when the
            genre isn't formally tagged.
        exclude_genres: drop titles matching ANY of these genres/themes.
        keywords: require at least one of these words to appear in the synopsis.
        seasonal: when true, restrict to the current season; otherwise search all years.
        max_episodes: drop titles with more than this many episodes.
        min_score: drop titles scored below this (0-10 scale).
        limit: maximum number of results to return (highest-scored first).
    """
    allow_explicit = ctx.deps.request.preferences.allow_explicit
    scope = f"{ctx.deps.season} {ctx.deps.year}" if seasonal else "all-time"
    label_genres = ", ".join(genres) if genres else "everything"
    await ctx.deps.emit(
        {
            "type": "tool",
            "tool": "search_catalog",
            "status": "started",
            "label": f"Searching {scope} catalog for {label_genres}",
        }
    )

    if seasonal:
        entries = await ctx.deps.catalog.get_seasonal(
            ctx.deps.season, ctx.deps.year, allow_explicit=allow_explicit
        )
    else:
        # Push genre filtering to AniList for all-time searches so results are
        # relevant rather than the globally top-scored titles.
        entries = await ctx.deps.catalog.search_all(
            genres=genres, per_page=max(limit, 50), allow_explicit=allow_explicit
        )

    filtered = _filter_entries(
        entries,
        include_genres=genres,
        exclude_genres=exclude_genres,
        keywords=keywords,
        max_episodes=max_episodes,
        min_score=min_score,
    )
    filtered.sort(key=lambda a: a.score or 0.0, reverse=True)
    results = filtered[:limit]

    # Record every result so the final output can be enriched authoritatively.
    for a in results:
        ctx.deps.store[a.id] = a

    await ctx.deps.emit(
        {
            "type": "tool",
            "tool": "search_catalog",
            "status": "finished",
            "label": f"Found {len(results)} matches in {scope} catalog",
            "count": len(results),
        }
    )
    return json.dumps([_to_dict(a) for a in results])


def _to_dict(a: AnimeEntry) -> dict[str, object]:
    return {
        "id": a.id,
        "title": a.title,
        "genres": a.genres,
        "tags": a.tags,
        "synopsis": a.synopsis[:_SYNOPSIS_LIMIT],
        "score": a.score,
        "episodes": a.episodes,
        "status": a.status,
        "cover_image": a.cover_image,
    }
