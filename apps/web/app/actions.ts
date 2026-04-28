"use server";

import { RecommendationResponseSchema } from "@shared-schemas";
import type { RecommendationResponse } from "@shared-schemas";

export type ActionState =
  | { status: "success"; data: RecommendationResponse }
  | { status: "error"; message: string }
  | null;

const API_URL = process.env["API_URL"] ?? "http://localhost:8000";

function parseGenres(raw: FormDataEntryValue | null): string[] {
  if (!raw) return [];
  return String(raw)
    .split(",")
    .map((g) => g.trim())
    .filter(Boolean);
}

export async function getRecommendations(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const body = {
    preferences: {
      liked_genres: parseGenres(formData.get("liked_genres")),
      disliked_genres: parseGenres(formData.get("disliked_genres")),
      notes: String(formData.get("notes") ?? ""),
    },
    top_n: Math.min(
      20,
      Math.max(1, parseInt(String(formData.get("top_n"))) || 10),
    ),
  };

  try {
    const res = await fetch(`${API_URL}/api/v1/recommend/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return {
        status: "error",
        message: (err as { detail?: string }).detail ?? `API error ${res.status}`,
      };
    }

    const data = RecommendationResponseSchema.parse(await res.json());
    return { status: "success", data };
  } catch (e) {
    return {
      status: "error",
      message: e instanceof Error ? e.message : "Unknown error occurred.",
    };
  }
}
