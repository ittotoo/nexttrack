import type { Track } from "../types/api";

interface TrackCardProps {
  track: Track;
  onPlay?: (track: Track) => void;
  action?: React.ReactNode;
  compact?: boolean;
}

export default function TrackCard({
  track,
  onPlay,
  action,
  compact,
}: TrackCardProps) {
  const artists = track.artists.join(", ");

  if (compact) {
    return (
      <div className="flex items-center justify-between gap-2 px-3 py-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-gray-900 truncate">
            {track.name}
          </p>
          <p className="text-xs text-gray-500 truncate">{artists}</p>
        </div>
        {action}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-3">
      <div className="min-w-0 flex-1">
        <p className="font-medium text-gray-900 truncate">{track.name}</p>
        <p className="text-sm text-gray-500 truncate">{artists}</p>
        <div className="flex items-center gap-2 mt-1 flex-wrap">
          {track.album && (
            <span className="text-xs text-gray-400 truncate max-w-[200px]">
              {track.album}
            </span>
          )}
          {track.genre && (
            <span className="inline-block rounded-full bg-brand-100 px-2 py-0.5 text-xs font-medium text-brand-700">
              {track.genre}
            </span>
          )}
          {track.popularity != null && (
            <span className="text-xs text-gray-400">
              Pop. {track.popularity}
            </span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {onPlay && (
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
        )}
        {action}
      </div>
    </div>
  );
}
