import type { Track, RecommendationItem } from "../types/api";
import RecommendationCard from "./RecommendationCard";

interface RecommendationListProps {
  recommendations: RecommendationItem[];
  processingTime: number | null;
  loading: boolean;
  error: string | null;
  onPlay: (track: Track) => void;
  isRandom?: boolean;
}

export default function RecommendationList({
  recommendations,
  processingTime,
  loading,
  error,
  onPlay,
  isRandom,
}: RecommendationListProps) {
  if (error) {
    return (
      <div
        className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        role="alert"
      >
        {error}
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12" aria-busy="true">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
        <span className="ml-3 text-sm text-gray-500">
          Generating recommendations...
        </span>
      </div>
    );
  }

  if (recommendations.length === 0) return null;

  return (
    <section aria-label="Recommendations">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold text-gray-900">
          {isRandom ? "Random Tracks" : "Recommendations"}
        </h2>
        {processingTime != null && (
          <span className="text-xs text-gray-400 tabular-nums">
            {processingTime.toFixed(0)}ms
          </span>
        )}
      </div>
      <div className="space-y-3" aria-live="polite">
        {recommendations.map((item, i) => (
          <RecommendationCard
            key={item.track.spotify_id}
            item={item}
            rank={i + 1}
            onPlay={onPlay}
          />
        ))}
      </div>
    </section>
  );
}
