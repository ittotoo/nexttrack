import type { Track } from "../types/api";
import TrackCard from "./TrackCard";

interface SeedTrackListProps {
  seeds: Track[];
  onRemove: (spotifyId: string) => void;
  onPlay: (track: Track) => void;
}

const MAX_SEEDS = 5;

export default function SeedTrackList({
  seeds,
  onRemove,
  onPlay,
}: SeedTrackListProps) {
  if (seeds.length === 0) {
    return (
      <div className="rounded-lg border-2 border-dashed border-gray-300 p-6 text-center text-sm text-gray-500">
        Search and select 1-5 tracks to get recommendations.
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold text-gray-700">
          Seed Tracks ({seeds.length}/{MAX_SEEDS})
        </h2>
        {seeds.length >= MAX_SEEDS && (
          <span className="text-xs text-amber-600 font-medium">
            Maximum reached
          </span>
        )}
      </div>
      <ul className="space-y-2" aria-label="Selected seed tracks">
        {seeds.map((track) => (
          <li key={track.spotify_id}>
            <TrackCard
              track={track}
              onPlay={onPlay}
              action={
                <button
                  onClick={() => onRemove(track.spotify_id)}
                  className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500 transition-colors"
                  aria-label={`Remove ${track.name}`}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="w-4 h-4"
                  >
                    <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                  </svg>
                </button>
              }
            />
          </li>
        ))}
      </ul>
    </div>
  );
}
