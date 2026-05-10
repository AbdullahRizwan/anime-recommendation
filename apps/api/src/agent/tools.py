import json
from dataclasses import dataclass, field

from pydantic_ai import RunContext

from src.domain.models import AnimeEntry, RecommendationRequest
from src.infrastructure.catalog_service import CatalogService

_SYNOPSIS_LIMIT = 300

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
    store: dict[int, AnimeEntry] = field(default_factory=dict)


async def get_seasonal_anime(ctx: RunContext[Deps], season: str, year: int) -> str:
    """Fetch seasonal anime catalog from AniList. Season must be WINTER, SPRING, SUMMER, or FALL."""
    anime_list = await ctx.deps.catalog.get_seasonal(season.upper(), year)
    ctx.deps.store = {a.id: a for a in anime_list}
    return json.dumps([_to_dict(a) for a in anime_list])


async def search_all_anime(
    ctx: RunContext[Deps],
    genres: list[str] | None = None,
    per_page: int = 50,
) -> str:
    """Search AniList's full catalog (all years) filtered by genre, sorted by score.
    Use this when the user wants classic or highly-rated anime beyond the current season."""
    anime_list = await ctx.deps.catalog.search_all(genres=genres, per_page=per_page)
    for a in anime_list:
        ctx.deps.store[a.id] = a
    return json.dumps([_to_dict(a) for a in anime_list])


async def filter_anime(
    ctx: RunContext[Deps],
    anime_ids: list[int],
    include_genres: list[str] | None = None,
    exclude_genres: list[str] | None = None,
    synopsis_keywords: list[str] | None = None,
    max_episodes: int | None = None,
) -> str:
    """Filter an anime list by genres, synopsis keywords, or episode count.
    synopsis_keywords checks if any keyword appears in the description (case-insensitive)."""
    include = {g.lower() for g in (include_genres or [])}
    exclude_set = {g.lower() for g in (exclude_genres or [])}
    explicit_kw = [k.lower() for k in (synopsis_keywords or [])]

    # Build derived keywords only for genres with explicit mappings.
    # Unmapped genres use tag-only matching so a genre name appearing
    # in an unrelated synopsis doesn't produce false positives.
    derived_kw: list[str] = []
    for g in include:
        derived_kw.extend(_GENRE_KEYWORDS.get(g, []))

    results = []
    for aid in anime_ids:
        a = ctx.deps.store.get(aid)
        if not a:
            continue
        genres = {g.lower() for g in a.genres}
        if exclude_set and exclude_set & genres:
            continue
        if max_episodes and a.episodes and a.episodes > max_episodes:
            continue
        synopsis_lower = a.synopsis.lower()
        if include:
            tag_match = bool(include & genres)
            synopsis_match = any(k in synopsis_lower for k in derived_kw)
            if not tag_match and not synopsis_match:
                continue
        if explicit_kw and not any(k in synopsis_lower for k in explicit_kw):
            continue
        results.append(a)
    return json.dumps([_to_dict(a) for a in results])


async def rank_anime(
    ctx: RunContext[Deps],
    anime_ids: list[int],
    top_n: int,
) -> str:
    """Get details for the model's top picks to rank."""
    picks = [ctx.deps.store[aid] for aid in anime_ids if aid in ctx.deps.store][:top_n]
    return json.dumps([_to_dict(a) for a in picks])


def _to_dict(a: AnimeEntry) -> dict[str, object]:
    return {
        "id": a.id,
        "title": a.title,
        "genres": a.genres,
        "synopsis": a.synopsis[:_SYNOPSIS_LIMIT],
        "score": a.score,
        "episodes": a.episodes,
        "status": a.status,
        "cover_image": a.cover_image,
    }
