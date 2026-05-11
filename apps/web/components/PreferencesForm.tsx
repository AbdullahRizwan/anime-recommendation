"use client";

import { useActionState } from "react";
import { getRecommendations } from "../app/actions";
import { RecommendationCard } from "./RecommendationCard";

export function PreferencesForm() {
  const [state, action, isPending] = useActionState(getRecommendations, null);

  return (
    <div>
      <form action={action} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Genres you like
            <span className="text-gray-400 font-normal"> — comma-separated</span>
          </label>
          <input
            name="liked_genres"
            type="text"
            placeholder="Action, Fantasy, Romance"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Genres to avoid
            <span className="text-gray-400 font-normal"> — comma-separated</span>
          </label>
          <input
            name="disliked_genres"
            type="text"
            placeholder="Ecchi, Horror"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Notes
          </label>
          <textarea
            name="notes"
            placeholder="e.g. prefer completed series, good pacing, no filler"
            rows={3}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            How many recommendations
          </label>
          <input
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
          {isPending ? "Finding anime… this takes ~15s" : "Get Recommendations"}
        </button>
      </form>

      {state?.status === "error" && (
        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {state.message}
        </div>
      )}

      {state?.status === "success" && (
        <div className="mt-8">
          <h2 className="text-xl font-bold text-gray-900">
            {state.data.season} {state.data.year}
          </h2>
          <p className="mt-1 text-sm text-gray-500 mb-5">
            {state.data.reasoning_summary}
          </p>
          <div className="space-y-4">
            {state.data.recommendations.map((rec) => (
              <RecommendationCard key={rec.id} rec={rec} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
