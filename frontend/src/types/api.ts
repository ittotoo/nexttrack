export interface AudioFeatures {
  acousticness: number;
  danceability: number;
  energy: number;
  instrumentalness: number;
  liveness: number;
  loudness: number;
  speechiness: number;
  valence: number;
  tempo: number;
  time_signature: number;
  key: number;
  mode: number;
  duration_ms: number;
}

export interface Track {
  spotify_id: string;
  name: string;
  artists: string[];
  album: string | null;
  release_date: string | null;
  genre: string | null;
  features: AudioFeatures | null;
  preview_url: string | null;
  popularity: number | null;
}

export interface RecommendationItem {
  track: Track;
  similarity_score: number;
  explanation: string;
  content_score: number | null;
  knowledge_score: number | null;
  popularity_score: number | null;
}

export interface RecommendationRequest {
  seed_track_ids: string[];
  limit: number;
  target_energy?: number;
  target_valence?: number;
  target_danceability?: number;
  diversity_weight: number;
}

export interface RecommendationResponse {
  recommendations: RecommendationItem[];
  seed_tracks: Track[];
  request_params: RecommendationRequest;
  processing_time_ms: number;
}
