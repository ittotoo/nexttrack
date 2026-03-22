"""NextTrack API - Privacy-Preserving Music Recommendation Service"""

import logging
import time
from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.track import Track
from app.models.request import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationItem,
)
from app.models.genres import Genre
from app.external.spotify import SpotifyClient
from app.recommender.hybrid_engine import HybridRecommendationEngine
from app.database import Database

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NextTrack API",
    description="Privacy-preserving stateless music recommendation service",
    version="1.0.0",
)

# CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Spotify client (singleton) - used as fallback
spotify_client = SpotifyClient()

# Initialize database connection
db = Database()


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "service": "NextTrack API",
        "version": "0.1.0",
        "status": "active",
        "description": "Privacy-preserving stateless music recommendation",
        "endpoints": {
            "POST /recommend": "Generate recommendations from seed tracks",
            "GET /track/{track_id}": "Get track details and audio features",
            "GET /search": "Search for tracks",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "nexttrack-api"}


@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest) -> RecommendationResponse:
    """Generate music recommendations based on seed tracks. """
    start_time = time.time()
    logger.info(f"Recommendation request: {len(request.seed_track_ids)} seed tracks")

    try:
        # Fetch seed tracks with audio features from DATABASE
        seed_tracks = db.get_tracks_by_spotify_ids(request.seed_track_ids)

        if not seed_tracks:
            raise HTTPException(
                status_code=404,
                detail="Could not find any of the provided seed tracks in database",
            )

        # Validate that at least one seed has audio features
        valid_seeds = [t for t in seed_tracks if t.features is not None]
        if not valid_seeds:
            raise HTTPException(
                status_code=400,
                detail="None of the seed tracks have audio features available",
            )

        logger.info(f"Fetched {len(seed_tracks)} seed tracks from database, {len(valid_seeds)} with features")

        # Get candidate tracks from DATABASE
        # Query database for candidates using similarity-based approach
        candidate_tracks = _get_candidate_tracks_from_db(
            seed_tracks=valid_seeds,
            request=request,
            limit=100,  # Larger pool for hybrid scoring (KG benefits from breadth)
        )

        logger.info(f"Fetched {len(candidate_tracks)} candidate tracks from database")

        # Initialize hybrid recommendation engine
        engine = HybridRecommendationEngine(
            candidate_pool=candidate_tracks, db=db
        )

        # Generate hybrid recommendations (40/30/30 ensemble)
        recommendations = engine.generate_recommendations(
            seed_tracks=valid_seeds, request=request
        )

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        logger.info(
            f"Generated {len(recommendations)} recommendations in {processing_time:.2f}ms"
        )

        return RecommendationResponse(
            recommendations=recommendations,
            seed_tracks=seed_tracks,
            request_params=request,
            processing_time_ms=processing_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/track/{track_id}", response_model=Track)
async def get_track(track_id: str) -> Track:
    """Get info about a specific track."""
    try:
        # Try database first (fast path)
        track = db.get_track_by_spotify_id(track_id)
        if track:
            logger.info(f"Track {track_id} found in database")
            return track

        # Fallback to Spotify API (slower, may not have audio features)
        logger.info(f"Track {track_id} not in database, trying Spotify API")
        track = spotify_client.get_track_with_features(track_id)
        if not track:
            raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
        return track
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching track {track_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search", response_model=List[Track])
async def search_tracks(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=20, ge=1, le=50, description="Number of results"),
    genre: Genre = Query(default=None, description="Filter by genre (113 available genres)"),
) -> List[Track]:
    """Search for tracks by name, artist, or keywords. """
    try:
        # Search database (convert enum to string value)
        genre_str = genre.value if genre else None
        tracks = db.search_tracks(query=q, genre=genre_str, limit=limit)
        logger.info(f"Found {len(tracks)} tracks in database for query '{q}' with genre '{genre_str}'")
        return tracks
    except Exception as e:
        logger.error(f"Error searching tracks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/random", response_model=List[Track])
async def random_tracks(
    limit: int = Query(default=5, ge=1, le=50, description="Number of random tracks"),
    exclude: str = Query(default="", description="Comma-separated Spotify IDs to exclude"),
) -> List[Track]:
    """Get random tracks from the database"""
    try:
        tracks = db.get_random_tracks(limit=limit)
        if exclude:
            exclude_ids = set(exclude.split(","))
            tracks = [t for t in tracks if t.spotify_id not in exclude_ids]
        return tracks
    except Exception as e:
        logger.error(f"Error fetching random tracks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_candidate_tracks_from_db(
    seed_tracks: List[Track],
    request: RecommendationRequest,
    limit: int = 500,
) -> List[Track]:
    """Get candidate tracks for recommendation from PostgreSQL database. """
    try:
        # Calculate average audio features from seed tracks
        from app.recommender.similarity import calculate_average_vector

        seed_vectors = [track.features.to_feature_vector() for track in seed_tracks]
        avg_vector = calculate_average_vector(seed_vectors)

        # Convert back to feature dict for database query
        feature_names = [
            "acousticness",
            "danceability",
            "energy",
            "instrumentalness",
            "liveness",
            "speechiness",
            "valence",
            "tempo",
        ]
        seed_features = {name: value for name, value in zip(feature_names, avg_vector)}

        # Get seed track IDs to exclude from results
        exclude_ids = [track.spotify_id for track in seed_tracks]

        # Query database for similar tracks
        candidates = db.get_similar_tracks_by_features(
            seed_features=seed_features,
            limit=limit,
            exclude_ids=exclude_ids,
        )

        logger.info(f"Database returned {len(candidates)} similar candidates")
        return candidates

    except Exception as e:
        logger.error(f"Error fetching candidate tracks from database: {e}", exc_info=True)
        # Fallback to random tracks if similarity fails
        logger.info("Falling back to random track selection")
        return db.get_random_tracks(limit=limit)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
