import type { RecommendationRequest, RecommendationResponse } from "@shared-schemas";
import { RecommendationResponseSchema } from "@shared-schemas";

const API_URL = process.env["API_URL"] ?? "http://localhost:8000";

export async function getRecommendations(
  request: RecommendationRequest,
): Promise<RecommendationResponse> {
  const res = await fetch(`${API_URL}/api/v1/recommend/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }

  return RecommendationResponseSchema.parse(await res.json());
}
