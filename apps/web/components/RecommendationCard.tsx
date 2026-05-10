import Image from "next/image";
import type { RankedAnime } from "@shared-schemas";

export function RecommendationCard({ rec }: { rec: RankedAnime }) {
  return (
    <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
      <div className="flex items-stretch gap-0">
        {rec.cover_image ? (
          <div className="relative w-24 shrink-0">
            <Image
              src={rec.cover_image}
              alt={rec.title}
              fill
              className="object-cover"
              sizes="96px"
            />
          </div>
        ) : (
          <div className="w-24 shrink-0 bg-gray-100 flex items-center justify-center text-gray-300 text-xs">
            No image
          </div>
        )}
        <div className="flex-1 min-w-0 p-4">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-2xl font-bold text-blue-600 leading-none shrink-0">
                #{rec.rank}
              </span>
              <h3 className="font-semibold text-gray-900 truncate">{rec.title}</h3>
            </div>
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
