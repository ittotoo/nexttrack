"""Tests for hybrid recommendation engine."""

import pytest
from unittest.mock import MagicMock

from app.recommender.hybrid_engine import (
    HybridRecommendationEngine,
    CONTENT_WEIGHT,
    KNOWLEDGE_WEIGHT,
    POPULARITY_WEIGHT,
)
from app.models.request import RecommendationRequest
from app.models.track import Track, AudioFeatures


def _make_track(spotify_id, energy=0.5, valence=0.5, popularity=50, genre="pop", db_id=None):
    """Helper to create a track with specified features."""
    return Track(
        spotify_id=spotify_id,
        name=f"Track {spotify_id}",
        artists=["Test Artist"],
        genre=genre,
        popularity=popularity,
        db_id=db_id,
        features=AudioFeatures(
            acousticness=0.5, danceability=0.5, energy=energy,
            instrumentalness=0.0, liveness=0.1, loudness=-8.0,
            speechiness=0.05, valence=valence, tempo=120.0,
            time_signature=4, key=0, mode=1, duration_ms=200000,
        ),
    )


def _mock_db():
    """Create a mock database that returns empty KG results."""
    mock = MagicMock()
    mock.get_artist_ids_for_tracks.return_value = {}
    mock.get_artist_relationships_bfs.return_value = []
    mock.get_candidate_artist_ids.return_value = {}
    return mock


class TestHybridWeights:
    """Tests for hybrid ensemble weight configuration."""

    def test_weights_sum_to_one(self):
        total = CONTENT_WEIGHT + KNOWLEDGE_WEIGHT + POPULARITY_WEIGHT
        assert total == pytest.approx(1.0)

    def test_content_weight_is_forty_percent(self):
        assert CONTENT_WEIGHT == 0.4

    def test_knowledge_weight_is_thirty_percent(self):
        assert KNOWLEDGE_WEIGHT == 0.3

    def test_popularity_weight_is_thirty_percent(self):
        assert POPULARITY_WEIGHT == 0.3


class TestHybridRecommendationEngine:
    """Tests for the HybridRecommendationEngine class."""

    def test_initialisation(self):
        candidates = [_make_track("t1"), _make_track("t2")]
        engine = HybridRecommendationEngine(candidate_pool=candidates, db=_mock_db())
        assert len(engine.candidate_pool) == 2

    def test_generates_recommendations(self):
        seed = _make_track("seed", energy=0.8, valence=0.7)
        candidates = [
            _make_track("c1", energy=0.75, valence=0.65, db_id=10),
            _make_track("c2", energy=0.3, valence=0.2, db_id=11),
        ]

        engine = HybridRecommendationEngine(candidate_pool=candidates, db=_mock_db())
        request = RecommendationRequest(seed_track_ids=["seed"], limit=2)

        results = engine.generate_recommendations(
            seed_tracks=[seed], request=request
        )

        assert len(results) > 0

    def test_recommendations_have_component_scores(self):
        seed = _make_track("seed", energy=0.8)
        candidate = _make_track("c1", energy=0.75, db_id=10)

        engine = HybridRecommendationEngine(candidate_pool=[candidate], db=_mock_db())
        request = RecommendationRequest(seed_track_ids=["seed"], limit=1)

        results = engine.generate_recommendations([seed], request)

        assert len(results) == 1
        item = results[0]
        assert item.content_score is not None
        assert item.knowledge_score is not None
        assert item.popularity_score is not None

    def test_similarity_score_is_weighted_combination(self):
        seed = _make_track("seed", energy=0.8, popularity=60)
        candidate = _make_track("c1", energy=0.75, popularity=60, db_id=10)

        engine = HybridRecommendationEngine(candidate_pool=[candidate], db=_mock_db())
        request = RecommendationRequest(seed_track_ids=["seed"], limit=1, diversity_weight=0.0)

        results = engine.generate_recommendations([seed], request)
        item = results[0]

        # Verify hybrid score = weighted sum of components
        expected = (
            CONTENT_WEIGHT * item.content_score
            + KNOWLEDGE_WEIGHT * item.knowledge_score
            + POPULARITY_WEIGHT * item.popularity_score
        )
        assert item.similarity_score == pytest.approx(expected, abs=0.001)

    def test_seed_tracks_excluded_from_results(self):
        seed = _make_track("seed", energy=0.8, db_id=1)
        candidates = [
            seed,  # Same track as seed
            _make_track("c1", energy=0.75, db_id=10),
        ]

        engine = HybridRecommendationEngine(candidate_pool=candidates, db=_mock_db())
        request = RecommendationRequest(seed_track_ids=["seed"], limit=5)

        results = engine.generate_recommendations([seed], request)

        result_ids = [r.track.spotify_id for r in results]
        assert "seed" not in result_ids

    def test_limit_respected(self):
        seed = _make_track("seed")
        candidates = [_make_track(f"c{i}", db_id=i+10) for i in range(20)]

        engine = HybridRecommendationEngine(candidate_pool=candidates, db=_mock_db())
        request = RecommendationRequest(seed_track_ids=["seed"], limit=5)

        results = engine.generate_recommendations([seed], request)
        assert len(results) <= 5

    def test_no_features_handled_gracefully(self):
        seed = _make_track("seed", energy=0.8)
        candidate = Track(
            spotify_id="no_features",
            name="No Features",
            artists=["Artist"],
            features=None,
            popularity=50,
            db_id=10,
        )

        engine = HybridRecommendationEngine(candidate_pool=[candidate], db=_mock_db())
        request = RecommendationRequest(seed_track_ids=["seed"], limit=1)

        # Should not raise
        results = engine.generate_recommendations([seed], request)
        assert isinstance(results, list)

    def test_empty_candidates_returns_empty(self):
        seed = _make_track("seed")

        engine = HybridRecommendationEngine(candidate_pool=[], db=_mock_db())
        request = RecommendationRequest(seed_track_ids=["seed"], limit=5)

        results = engine.generate_recommendations([seed], request)
        assert len(results) == 0

    def test_explanations_present(self):
        seed = _make_track("seed", energy=0.8, valence=0.7, popularity=70)
        candidate = _make_track("c1", energy=0.75, valence=0.65, popularity=72, db_id=10)

        engine = HybridRecommendationEngine(candidate_pool=[candidate], db=_mock_db())
        request = RecommendationRequest(seed_track_ids=["seed"], limit=1)

        results = engine.generate_recommendations([seed], request)
        assert len(results) == 1
        assert results[0].explanation  # Non-empty explanation

    def test_diversity_weight_zero_is_pure_relevance(self):
        seed = _make_track("seed", energy=0.8)
        c1 = _make_track("c1", energy=0.79, db_id=10)  # Very similar
        c2 = _make_track("c2", energy=0.2, db_id=11)   # Very different

        engine = HybridRecommendationEngine(candidate_pool=[c1, c2], db=_mock_db())

        # With diversity=0, c1 should always be first (more similar)
        request = RecommendationRequest(seed_track_ids=["seed"], limit=2, diversity_weight=0.0)
        results = engine.generate_recommendations([seed], request)

        assert results[0].track.spotify_id == "c1"

    def test_content_fallback_when_kg_unavailable(self):
        """When no KG data exists, content and popularity still drive results."""
        seed = _make_track("seed", energy=0.8, popularity=70)
        c1 = _make_track("c1", energy=0.79, popularity=72, db_id=10)

        # DB returns no KG data
        engine = HybridRecommendationEngine(candidate_pool=[c1], db=_mock_db())
        request = RecommendationRequest(seed_track_ids=["seed"], limit=1)

        results = engine.generate_recommendations([seed], request)
        assert len(results) == 1
        assert results[0].knowledge_score == pytest.approx(0.0, abs=0.01)
        assert results[0].content_score > 0
        assert results[0].popularity_score > 0
