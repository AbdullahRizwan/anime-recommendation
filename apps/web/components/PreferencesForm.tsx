"use client";

import { RecommendationResponseSchema } from "@shared-schemas";
import type { RecommendationResponse } from "@shared-schemas";
import { useRef, useState } from "react";
import { RecommendationCard } from "./RecommendationCard";

type Activity = { id: number; label: string; status: "running" | "done" };

// Events streamed from POST /api/recommend/stream (proxied to FastAPI SSE).
type StreamEvent =
  | { type: "tool"; tool: string; status: "started" | "finished"; label: string; count?: number }
  | { type: "complete"; data: unknown }
  | { type: "error"; message: string };

function parseGenres(raw: string): string[] {
  return raw
    .split(",")
    .map((g) => g.trim())
    .filter(Boolean);
}

function ProgressSteps({ activities, pending }: { activities: Activity[]; pending: boolean }) {
  if (!pending && activities.length === 0) return null;
  return (
    <div className="mt-4 space-y-2">
      {activities.map((a) => (
        <div
          key={a.id}
          className={`flex items-center gap-2.5 text-sm transition-colors ${
            a.status === "done" ? "text-green-600" : "text-blue-600"
          }`}
        >
          {a.status === "done" ? (
            <svg
              aria-hidden="true"
              className="w-4 h-4 shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          ) : (
            <svg
              aria-hidden="true"
              className="w-4 h-4 shrink-0 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
              />
            </svg>
          )}
          <span className={a.status === "done" ? "" : "font-medium"}>{a.label}</span>
        </div>
      ))}
      {pending && activities.length === 0 && (
        <div className="flex items-center gap-2.5 text-sm text-blue-600">
          <svg
            aria-hidden="true"
            className="w-4 h-4 shrink-0 animate-spin"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
            />
          </svg>
          <span className="font-medium">Thinking…</span>
        </div>
      )}
    </div>
  );
}

export function PreferencesForm() {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);
  const idRef = useRef(0);

  function handleEvent(evt: StreamEvent) {
    if (evt.type === "tool") {
      if (evt.status === "started") {
        const id = idRef.current++;
        setActivities((prev) => [...prev, { id, label: evt.label, status: "running" }]);
      } else {
        setActivities((prev) => {
          const next = [...prev];
          for (let i = next.length - 1; i >= 0; i--) {
            const item = next[i];
            if (item && item.status === "running") {
              next[i] = { ...item, label: evt.label, status: "done" };
              break;
            }
          }
          return next;
        });
      }
    } else if (evt.type === "complete") {
      const parsed = RecommendationResponseSchema.safeParse(evt.data);
      if (parsed.success) {
        setResult(parsed.data);
      } else {
        setError("The server returned a malformed response.");
      }
    } else if (evt.type === "error") {
      setError(evt.message || "Something went wrong.");
    }
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);

    setActivities([]);
    setResult(null);
    setError(null);
    setIsPending(true);

    const body = {
      preferences: {
        liked_genres: parseGenres(String(fd.get("liked_genres") ?? "")),
        disliked_genres: parseGenres(String(fd.get("disliked_genres") ?? "")),
        notes: String(fd.get("notes") ?? ""),
        allow_explicit: fd.get("allow_explicit") === "on",
      },
      top_n: Math.min(20, Math.max(1, Number.parseInt(String(fd.get("top_n"))) || 10)),
    };

    try {
      const res = await fetch("/api/recommend/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok || !res.body) {
        setError(`Request failed (${res.status}).`);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const part of parts) {
          const dataLine = part.split("\n").find((l) => l.startsWith("data:"));
          if (!dataLine) continue;
          const payload = dataLine.slice(5).trim();
          if (!payload) continue;
          try {
            handleEvent(JSON.parse(payload) as StreamEvent);
          } catch {
            // ignore malformed chunk
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error occurred.");
    } finally {
      setIsPending(false);
    }
  }

  return (
    <div>
      <form onSubmit={onSubmit} className="space-y-5">
        <div>
          <label htmlFor="liked_genres" className="block text-sm font-medium text-gray-700 mb-1">
            Genres you like
            <span className="text-gray-400 font-normal"> — comma-separated</span>
          </label>
          <input
            id="liked_genres"
            name="liked_genres"
            type="text"
            placeholder="Action, Fantasy, Romance"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label htmlFor="disliked_genres" className="block text-sm font-medium text-gray-700 mb-1">
            Genres to avoid
            <span className="text-gray-400 font-normal"> — comma-separated</span>
          </label>
          <input
            id="disliked_genres"
            name="disliked_genres"
            type="text"
            placeholder="Ecchi, Horror"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
            Notes
          </label>
          <textarea
            id="notes"
            name="notes"
            placeholder="e.g. prefer completed series, good pacing, no filler"
            rows={3}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
          />
        </div>

        <div>
          <label htmlFor="top_n" className="block text-sm font-medium text-gray-700 mb-1">
            How many recommendations
          </label>
          <input
            id="top_n"
            name="top_n"
            type="number"
            defaultValue={5}
            min={1}
            max={20}
            className="w-24 rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <input
            id="allow_explicit"
            name="allow_explicit"
            type="checkbox"
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="allow_explicit" className="text-sm text-gray-700">
            Include explicit content (Ecchi, Hentai)
          </label>
        </div>

        <button
          type="submit"
          disabled={isPending}
          className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
        >
          {isPending ? "Working…" : "Get Recommendations"}
        </button>
        <ProgressSteps activities={activities} pending={isPending} />
      </form>

      {error && (
        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-8">
          <h2 className="text-xl font-bold text-gray-900">
            {result.season} {result.year}
          </h2>
          <p className="mt-1 text-sm text-gray-500 mb-5">{result.reasoning_summary}</p>
          <div className="space-y-4">
            {result.recommendations.map((rec) => (
              <RecommendationCard key={rec.id} rec={rec} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
