"""Models for tracks and their audio features."""

from typing import List, Optional
from pydantic import BaseModel, Field


class AudioFeatures(BaseModel):
    """Subset of Spotify audio features used in the app."""

    # Main audio characteritics
    acousticness: float = Field(ge=0.0, le=1.0, description="Confidence measure of acoustic content")
    danceability: float = Field(ge=0.0, le=1.0, description="How suitable for dancing")
    energy: float = Field(ge=0.0, le=1.0, description="Intensity and activity measure")
    instrumentalness: float = Field(ge=0.0, le=1.0, description="Predicts lack of vocals")
    
    # Less frequently used but still useful
    liveness: float = Field(ge=0.0, le=1.0, description="Presence of audience")
    loudness: float = Field(description="Overall loudness in decibels")
    speechiness: float = Field(ge=0.0, le=1.0, description="Presence of spoken words")
    valence: float = Field(ge=0.0, le=1.0, description="Musical positiveness/happiness")

    # Tempo and Rhythm
    tempo: float = Field(gt=0, description="Estimated tempo in BPM")
    time_signature: int = Field(ge=0, le=7, description="Estimated time signature")

    # Key and Mode
    key: int = Field(ge=-1, le=11, description="Estimated key (-1 if no key detected)")
    mode: int = Field(ge=0, le=1, description="0 = minor, 1 = major")

    duration_ms: int = Field(gt=0, description="Duration in milliseconds")

    def to_feature_vector(self) -> List[float]:
        """Return a simplified feature vector for similarity comparisons."""
        return [
            self.acousticness,
            self.danceability,
            self.energy,
            self.instrumentalness,
            self.liveness,
            self.speechiness,
            self.valence,
            self.tempo / 200.0,  # Normalize tempo (max ~200 BPM) - experiment with different scaling for tempo
        ]


class Track(BaseModel):
    """Basic track model"""

    spotify_id: str = Field(description="Spotify track ID")
    name: str = Field(description="Track name")

    artists: List[str] = Field(description="List of artist names")

    album: Optional[str] = Field(default=None, description="Album name")
    release_date: Optional[str] = Field(default=None, description="Release date")

    genre: Optional[str] = Field(default=None, description="Track genre")

    features: Optional[AudioFeatures] = Field(default=None, description="Audio features from Spotify")

    preview_url: Optional[str] = Field(default=None, description="30-second preview URL")

    popularity: Optional[int] = Field(default=None, ge=0, le=100, description="Spotify popularity score")

    # Internal database ID
    db_id: Optional[int] = Field(default=None, exclude=True)

    @property
    def display_name(self) -> str:
        artist_str = ", ".join(self.artists)
        return f"{self.name} - {artist_str}"
