import type {
  Track,
  RecommendationRequest,
  RecommendationResponse,
} from "../types/api";

const API_BASE = "/api";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail ?? "Request failed");
  }

  return response.json() as Promise<T>;
}

export async function searchTracks(
  query: string,
  genre?: string,
  limit = 20,
): Promise<Track[]> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  if (genre) params.set("genre", genre);
  return request<Track[]>(`/search?${params}`);
}

export async function getTrack(trackId: string): Promise<Track> {
  return request<Track>(`/track/${encodeURIComponent(trackId)}`);
}

export async function getRecommendations(
  body: RecommendationRequest,
): Promise<RecommendationResponse> {
  return request<RecommendationResponse>("/recommend", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getRandomTracks(
  limit = 5,
  excludeIds: string[] = [],
): Promise<Track[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (excludeIds.length > 0) params.set("exclude", excludeIds.join(","));
  return request<Track[]>(`/random?${params}`);
}

export async function healthCheck(): Promise<boolean> {
  try {
    await request<{ status: string }>("/health");
    return true;
  } catch {
    return false;
  }
}
