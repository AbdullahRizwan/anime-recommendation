from typing import Any


def get_tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_seasonal_anime",
                "description": "Fetch seasonal anime catalog from AniList.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "season": {
                            "type": "string",
                            "enum": ["WINTER", "SPRING", "SUMMER", "FALL"],
                        },
                        "year": {"type": "integer"},
                    },
                    "required": ["season", "year"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "filter_anime",
                "description": "Filter an anime list by genres or episode count.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "anime_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                        },
                        "include_genres": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "exclude_genres": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "max_episodes": {
                            "anyOf": [{"type": "integer"}, {"type": "null"}],
                        },
                    },
                    "required": ["anime_ids"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "rank_anime",
                "description": "Get details for the model's top picks to rank.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "anime_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                        },
                        "top_n": {"type": "integer"},
                    },
                    "required": ["anime_ids", "top_n"],
                },
            },
        },
    ]
