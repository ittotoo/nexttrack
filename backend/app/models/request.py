"""Request and response models for recommendation endpoint."""

from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.track import Track


class RecommendationRequest(BaseModel):
    """Request for music recommendations.  """

    # Seed Tracks (Required)
    seed_track_ids: List[str] = Field(
        min_length=1,
        max_length=5,
        description="1-5 Spotify track IDs to base recommendations on",
    )

    # Number of Recommendations
    limit: int = Field(default=10, ge=1, le=50, description="Number of recommendations to return")

    # Optional Preference Adjustments
    target_energy: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Target energy level (0=calm, 1=energetic)",
    )
    target_valence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Target mood (0=sad, 1=happy)",
    )
    target_danceability: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Target danceability",
    )

    # Diversity Control
    diversity_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for diversity vs similarity (0=maximize similarity, 1=maximize diversity)",
    )


class RecommendationItem(BaseModel):
    """Single recommendation with explanation."""

    track: Track
    similarity_score: float = Field(ge=0.0, le=1.0, description="Overall hybrid similarity score")
    explanation: str = Field(description="Human-readable explanation of recommendation")

    # Component scores for transparency
    content_score: Optional[float] = Field(default=None, description="Content-based component score (40%)")
    knowledge_score: Optional[float] = Field(default=None, description="Knowledge graph component score (30%)")
    popularity_score: Optional[float] = Field(default=None, description="Popularity component score (30%)")


class RecommendationResponse(BaseModel):
    """Response containing music recommendations."""

    recommendations: List[RecommendationItem]
    seed_tracks: List[Track] = Field(description="The seed tracks used")
    request_params: RecommendationRequest = Field(description="Original request parameters")

    # Performance Metrics
    processing_time_ms: float = Field(description="Time taken to generate recommendations")
