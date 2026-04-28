import type { RankedAnime } from "@shared-schemas";

export function RecommendationCard({ rec }: { rec: RankedAnime }) {
  return (
    <div className="rounded-xl border bg-white p-5 shadow-sm">
      <div className="flex items-start gap-4">
        <span className="text-3xl font-bold text-blue-600 leading-none w-10 shrink-0">
          #{rec.rank}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-semibold text-gray-900 truncate">{rec.title}</h3>
            <span className="text-sm font-medium text-gray-500 shrink-0">
              ★ {rec.score.toFixed(1)}
            </span>
          </div>
          <p className="mt-2 text-sm text-gray-600 leading-relaxed">{rec.reasoning}</p>
        </div>
      </div>
    </div>
  );
}
