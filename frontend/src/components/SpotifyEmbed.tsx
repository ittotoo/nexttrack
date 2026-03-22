import type { Track } from "../types/api";

interface SpotifyEmbedProps {
  track: Track | null;
  onClose: () => void;
}

export default function SpotifyEmbed({ track, onClose }: SpotifyEmbedProps) {
  if (!track) return null;

  const embedUrl = `https://open.spotify.com/embed/track/${track.spotify_id}?theme=0`;

  return (
    <div className="fixed bottom-0 inset-x-0 z-30 border-t border-gray-300 bg-white shadow-lg">
      <div className="max-w-5xl mx-auto flex items-center gap-2 px-4 py-1">
        <div className="flex-1 min-w-0">
          <iframe
            title={`Now playing: ${track.name}`}
            src={embedUrl}
            width="100%"
            height="80"
            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
            loading="lazy"
            className="rounded"
          />
        </div>
        <button
          onClick={onClose}
          className="shrink-0 rounded p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
          aria-label="Close player"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="w-5 h-5"
          >
            <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
