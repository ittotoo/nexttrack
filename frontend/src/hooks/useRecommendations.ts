import { useState, useCallback } from "react";
import type { Track, RecommendationItem, RecommendationRequest } from "../types/api";
import { getRecommendations, getRandomTracks } from "../services/api";

interface UseRecommendationsReturn {
  recommendations: RecommendationItem[];
  processingTime: number | null;
  loading: boolean;
  error: string | null;
  isRandom: boolean;
  generate: (request: RecommendationRequest) => Promise<void>;
  generateRandom: (limit: number, excludeIds: string[]) => Promise<void>;
  clear: () => void;
}

export function useRecommendations(): UseRecommendationsReturn {
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>(
    [],
  );
  const [processingTime, setProcessingTime] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRandom, setIsRandom] = useState(false);

  const generate = useCallback(async (request: RecommendationRequest) => {
    setLoading(true);
    setError(null);
    setIsRandom(false);
    try {
      const response = await getRecommendations(request);
      setRecommendations(response.recommendations);
      setProcessingTime(response.processing_time_ms);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get recommendations");
      setRecommendations([]);
      setProcessingTime(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const generateRandom = useCallback(
    async (limit: number, excludeIds: string[]) => {
      setLoading(true);
      setError(null);
      setIsRandom(true);
      try {
        const tracks = await getRandomTracks(limit, excludeIds);
        const items: RecommendationItem[] = tracks.map(
          (track: Track): RecommendationItem => ({
            track,
            similarity_score: 0,
            explanation: "Randomly selected track",
            content_score: null,
            knowledge_score: null,
            popularity_score: null,
          }),
        );
        setRecommendations(items);
        setProcessingTime(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to get random tracks",
        );
        setRecommendations([]);
        setProcessingTime(null);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const clear = useCallback(() => {
    setRecommendations([]);
    setProcessingTime(null);
    setError(null);
    setIsRandom(false);
  }, []);

  return {
    recommendations,
    processingTime,
    loading,
    error,
    isRandom,
    generate,
    generateRandom,
    clear,
  };
}
