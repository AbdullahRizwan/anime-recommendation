class AnimeTriageError(Exception):
    """Base exception for all domain errors."""


class AniListError(AnimeTriageError):
    """AniList API is unreachable or returned an error."""


class AgentError(AnimeTriageError):
    """The LLM agent failed or returned an unparseable response."""
