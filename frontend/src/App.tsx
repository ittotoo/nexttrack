import { useState, useCallback } from "react";
import type { Track, RecommendationRequest } from "./types/api";
import Header from "./components/Header";
import SearchBar from "./components/SearchBar";
import SeedTrackList from "./components/SeedTrackList";
import PreferenceControls from "./components/PreferenceControls";
import type { Preferences } from "./components/PreferenceControls";
import RecommendationList from "./components/RecommendationList";
import SpotifyEmbed from "./components/SpotifyEmbed";
import { useRecommendations } from "./hooks/useRecommendations";

const MAX_SEEDS = 5;

const DEFAULT_PREFS: Preferences = {
  diversity_weight: 0.3,
  target_energy: undefined,
  target_valence: undefined,
  target_danceability: undefined,
  limit: 10,
};

export default function App() {
  const [seeds, setSeeds] = useState<Track[]>([]);
  const [preferences, setPreferences] = useState<Preferences>(DEFAULT_PREFS);
  const [currentTrack, setCurrentTrack] = useState<Track | null>(null);
  const {
    recommendations,
    processingTime,
    loading,
    error,
    isRandom,
    generate,
    generateRandom,
    clear,
  } = useRecommendations();

  const addSeed = useCallback(
    (track: Track) => {
      setSeeds((prev) => {
        if (prev.length >= MAX_SEEDS) return prev;
        if (prev.some((t) => t.spotify_id === track.spotify_id)) return prev;
        return [...prev, track];
      });
    },
    [],
  );

  const removeSeed = useCallback((spotifyId: string) => {
    setSeeds((prev) => prev.filter((t) => t.spotify_id !== spotifyId));
  }, []);

  const handleGenerate = useCallback(() => {
    if (seeds.length === 0) return;
    const request: RecommendationRequest = {
      seed_track_ids: seeds.map((t) => t.spotify_id),
      limit: preferences.limit,
      diversity_weight: preferences.diversity_weight,
      target_energy: preferences.target_energy,
      target_valence: preferences.target_valence,
      target_danceability: preferences.target_danceability,
    };
    generate(request);
  }, [seeds, preferences, generate]);

  const handleRandom = useCallback(() => {
    const excludeIds = seeds.map((t) => t.spotify_id);
    generateRandom(preferences.limit, excludeIds);
  }, [seeds, preferences.limit, generateRandom]);

  return (
    <div className={`min-h-screen ${currentTrack ? "pb-24" : ""}`}>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-white focus:px-4 focus:py-2 focus:text-brand-700"
      >
        Skip to main content
      </a>

      <Header />

      <main id="main-content" className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {/* Search */}
        <section aria-label="Search for tracks">
          <SearchBar
            onSelect={addSeed}
            disabled={seeds.length >= MAX_SEEDS}
          />
        </section>

        {/* Seed tracks */}
        <SeedTrackList
          seeds={seeds}
          onRemove={removeSeed}
          onPlay={setCurrentTrack}
        />

        {/* Preferences */}
        <PreferenceControls
          value={preferences}
          onChange={setPreferences}
        />

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleGenerate}
            disabled={seeds.length === 0 || loading}
            className="flex-1 rounded-lg bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading && !isRandom ? "Generating..." : "Get Recommendations"}
          </button>
          <button
            onClick={handleRandom}
            disabled={loading}
            className="rounded-lg border border-gray-300 bg-white px-6 py-3 text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading && isRandom ? "Loading..." : "Random"}
          </button>
          {recommendations.length > 0 && (
            <button
              onClick={clear}
              className="rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm text-gray-500 hover:bg-gray-50 hover:text-red-500 transition-colors"
              aria-label="Clear recommendations"
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
          )}
        </div>

        {/* Results */}
        <RecommendationList
          recommendations={recommendations}
          processingTime={processingTime}
          loading={loading}
          error={error}
          onPlay={setCurrentTrack}
          isRandom={isRandom}
        />
      </main>

      {/* Persistent player */}
      <SpotifyEmbed
        track={currentTrack}
        onClose={() => setCurrentTrack(null)}
      />
    </div>
  );
}
