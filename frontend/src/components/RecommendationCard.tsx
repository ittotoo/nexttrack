import type { Track, RecommendationItem } from "../types/api";
import ScoreBreakdown from "./ScoreBreakdown";

interface RecommendationCardProps {
  item: RecommendationItem;
  rank: number;
  onPlay: (track: Track) => void;
}

export default function RecommendationCard({
  item,
  rank,
  onPlay,
}: RecommendationCardProps) {
  const { track } = item;
  const artists = track.artists.join(", ");
  const score = Math.round(item.similarity_score * 100);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-start gap-3">
        {/* Rank badge */}
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">
          {rank}
        </span>

        {/* Track info */}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="font-semibold text-gray-900 truncate">
                {track.name}
              </p>
              <p className="text-sm text-gray-500 truncate">{artists}</p>
              <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                {track.album && (
                  <span className="text-xs text-gray-400 truncate max-w-[180px]">
                    {track.album}
                  </span>
                )}
                {track.genre && (
                  <span className="inline-block rounded-full bg-brand-100 px-2 py-0.5 text-xs font-medium text-brand-700">
                    {track.genre}
                  </span>
                )}
              </div>
            </div>

            {/* Score + play */}
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-lg font-bold text-brand-600 tabular-nums">
                {score}%
              </span>
              <button
                onClick={() => onPlay(track)}
                className="rounded-full bg-brand-600 p-2 text-white hover:bg-brand-700 transition-colors"
                aria-label={`Play ${track.name}`}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="w-4 h-4"
                >
                  <path d="M6.3 2.84A1.5 1.5 0 004 4.11v11.78a1.5 1.5 0 002.3 1.27l9.344-5.891a1.5 1.5 0 000-2.538L6.3 2.841z" />
                </svg>
              </button>
            </div>
          </div>

          {/* Explanation */}
          <p className="mt-2 text-sm text-gray-600 italic">
            {item.explanation}
          </p>

          {/* Score breakdown */}
          <div className="mt-3">
            <ScoreBreakdown
              content={item.content_score}
              knowledge={item.knowledge_score}
              popularity={item.popularity_score}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
