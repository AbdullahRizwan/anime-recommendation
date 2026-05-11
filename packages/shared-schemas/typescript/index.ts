import { z } from "zod";

export const UserPreferencesSchema = z.object({
  liked_genres: z.array(z.string()).default([]),
  disliked_genres: z.array(z.string()).default([]),
  notes: z.string().default(""),
  allow_explicit: z.boolean().default(false),
});

export const RankedAnimeSchema = z.object({
  id: z.number().int(),
  title: z.string(),
  rank: z.number().int().positive(),
  score: z.number(),
  reasoning: z.string(),
  cover_image: z.string().nullable().optional(),
});

export const RecommendationRequestSchema = z.object({
  preferences: UserPreferencesSchema,
  season: z.string().nullable().optional(),
  year: z.number().int().nullable().optional(),
  top_n: z.number().int().min(1).max(50).default(10),
});

export const RecommendationResponseSchema = z.object({
  recommendations: z.array(RankedAnimeSchema),
  season: z.string(),
  year: z.number().int(),
  reasoning_summary: z.string(),
});

export type UserPreferences = z.infer<typeof UserPreferencesSchema>;
export type RankedAnime = z.infer<typeof RankedAnimeSchema>;
export type RecommendationRequest = z.infer<typeof RecommendationRequestSchema>;
export type RecommendationResponse = z.infer<typeof RecommendationResponseSchema>;
