"""Pytest configuration and fixtures for NextTrack tests."""

import pytest
from app.models.track import Track, AudioFeatures


@pytest.fixture
def sample_audio_features_1():
    """Sample audio features for testing (energetic, happy track)."""
    return AudioFeatures(
        acousticness=0.1,
        danceability=0.8,
        energy=0.9,
        instrumentalness=0.0,
        liveness=0.1,
        loudness=-5.0,
        speechiness=0.05,
        valence=0.8,
        tempo=128.0,
        time_signature=4,
        key=5,
        mode=1,
        duration_ms=180000,
    )


@pytest.fixture
def sample_audio_features_2():
    """Sample audio features for testing (calm, melancholic track)."""
    return AudioFeatures(
        acousticness=0.8,
        danceability=0.3,
        energy=0.2,
        instrumentalness=0.6,
        liveness=0.05,
        loudness=-12.0,
        speechiness=0.03,
        valence=0.2,
        tempo=72.0,
        time_signature=4,
        key=2,
        mode=0,
        duration_ms=240000,
    )


@pytest.fixture
def sample_audio_features_3():
    """Sample audio features for testing (moderate, balanced track)."""
    return AudioFeatures(
        acousticness=0.4,
        danceability=0.6,
        energy=0.6,
        instrumentalness=0.2,
        liveness=0.15,
        loudness=-8.0,
        speechiness=0.04,
        valence=0.5,
        tempo=100.0,
        time_signature=4,
        key=7,
        mode=1,
        duration_ms=200000,
    )


@pytest.fixture
def sample_track_1(sample_audio_features_1):
    """Sample track 1 (energetic, happy)."""
    return Track(
        spotify_id="track1",
        name="Energetic Track",
        artists=["Artist A"],
        album="Album 1",
        release_date="2023-01-01",
        genre="electronic",
        preview_url="https://example.com/preview1.mp3",
        popularity=85,
        features=sample_audio_features_1,
        db_id=1,
    )


@pytest.fixture
def sample_track_2(sample_audio_features_2):
    """Sample track 2 (calm, melancholic)."""
    return Track(
        spotify_id="track2",
        name="Calm Track",
        artists=["Artist B"],
        album="Album 2",
        release_date="2023-02-01",
        genre="ambient",
        preview_url="https://example.com/preview2.mp3",
        popularity=65,
        features=sample_audio_features_2,
        db_id=2,
    )


@pytest.fixture
def sample_track_3(sample_audio_features_3):
    """Sample track 3 (moderate, balanced)."""
    return Track(
        spotify_id="track3",
        name="Moderate Track",
        artists=["Artist C"],
        album="Album 3",
        release_date="2023-03-01",
        genre="rock",
        preview_url="https://example.com/preview3.mp3",
        popularity=75,
        features=sample_audio_features_3,
        db_id=3,
    )


@pytest.fixture
def sample_tracks(sample_track_1, sample_track_2, sample_track_3):
    """List of sample tracks for testing."""
    return [sample_track_1, sample_track_2, sample_track_3]


# === Knowledge Graph Test Fixtures ===

@pytest.fixture
def mock_artist_mapping():
    """Mock artist ID mapping for tracks. """
    return {
        "track1": [10, 11],
        "track2": [20],
        "track3": [30],
    }


@pytest.fixture
def mock_candidate_artist_mapping():
    """Mock candidate track db_id -> artist ID mapping."""
    return {
        1: [10, 11],
        2: [20],
        3: [30],
    }


@pytest.fixture
def mock_bfs_results():
    """Mock BFS traversal results from seed artists """
    return [
        {"artist_id": 20, "depth": 1, "weight": 1.0, "relationship_type": "collaboration"},
        {"artist_id": 30, "depth": 2, "weight": 0.7, "relationship_type": "shared_album"},
    ]
