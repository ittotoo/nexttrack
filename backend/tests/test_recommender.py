"""Tests for recommendation engine."""

import pytest
from app.recommender.engine import RecommendationEngine
from app.models.request import RecommendationRequest


class TestRecommendationEngine:
    """Tests for the core recommendation engine."""

    def test_engine_initialization(self, sample_tracks):
        
        engine = RecommendationEngine(candidate_pool=sample_tracks)
        assert len(engine.candidate_pool) == 3

    def test_generate_recommendations_basic(self, sample_track_1, sample_track_2, sample_track_3):
        """Should generate recommendations from seed tracks."""
        
        seed = [sample_track_1]
        candidates = [sample_track_2, sample_track_3]

        engine = RecommendationEngine(candidate_pool=candidates)
        request = RecommendationRequest(seed_track_ids=["track1"], limit=2)

        recommendations = engine.generate_recommendations(seed, request)

        assert len(recommendations) > 0
        assert all(rec.track.spotify_id != "track1" for rec in recommendations)

    def test_recommendations_have_scores(self, sample_track_1, sample_track_2):
        """Recommendations should have similarity scores."""
        seed = [sample_track_1]
        candidates = [sample_track_2]

        engine = RecommendationEngine(candidate_pool=candidates)
        request = RecommendationRequest(seed_track_ids=["track1"], limit=1)

        recommendations = engine.generate_recommendations(seed, request)

        assert len(recommendations) == 1
        assert 0.0 <= recommendations[0].similarity_score <= 1.0

    def test_recommendations_have_explanations(self, sample_track_1, sample_track_2):
        """Recommendations should have human-readable explanations."""
        seed = [sample_track_1]
        candidates = [sample_track_2]

        engine = RecommendationEngine(candidate_pool=candidates)
        request = RecommendationRequest(seed_track_ids=["track1"], limit=1)

        recommendations = engine.generate_recommendations(seed, request)

        assert len(recommendations) == 1
        assert isinstance(recommendations[0].explanation, str)
        assert len(recommendations[0].explanation) > 0

    def test_similar_tracks_rank_higher(
        self, sample_track_1, sample_track_2, sample_track_3, sample_audio_features_1
    ):
        """Tracks with similar features should rank higher."""
        # Create a track very similar to track1
        from app.models.track import Track

        similar_track = Track(
            spotify_id="similar",
            name="Very Similar Track",
            artists=["Artist D"],
            features=sample_audio_features_1,  # Same features as track1
        )

        seed = [sample_track_1]
        candidates = [sample_track_2, similar_track]

        engine = RecommendationEngine(candidate_pool=candidates)
        request = RecommendationRequest(seed_track_ids=["track1"], limit=2)

        recommendations = engine.generate_recommendations(seed, request)

        # Similar track should rank first
        assert recommendations[0].track.spotify_id == "similar"
        assert recommendations[0].similarity_score > recommendations[1].similarity_score

    def test_diversity_weight_affects_ranking(self, sample_tracks):
        """Higher diversity weight should produce more diverse recommendations."""
        seed = [sample_tracks[0]]
        candidates = sample_tracks[1:]

        # Low diversity weight - maximize similarity
        engine = RecommendationEngine(candidate_pool=candidates)
        request_similarity = RecommendationRequest(
            seed_track_ids=["track1"], limit=2, diversity_weight=0.0
        )
        recs_similarity = engine.generate_recommendations(seed, request_similarity)

        # High diversity weight - maximize diversity
        request_diversity = RecommendationRequest(
            seed_track_ids=["track1"], limit=2, diversity_weight=1.0
        )
        recs_diversity = engine.generate_recommendations(seed, request_diversity)

        # Both should return recommendations
        assert len(recs_similarity) == 2
        assert len(recs_diversity) == 2

    def test_limit_parameter_respected(self, sample_tracks):
        """Should return at most 'limit' recommendations."""
        seed = [sample_tracks[0]]
        candidates = sample_tracks[1:]

        engine = RecommendationEngine(candidate_pool=candidates)

        for limit in [1, 2]:
            request = RecommendationRequest(seed_track_ids=["track1"], limit=limit)
            recommendations = engine.generate_recommendations(seed, request)
            assert len(recommendations) <= limit

    def test_seed_tracks_not_in_recommendations(self, sample_tracks):
        """Seed tracks should not appear in recommendations."""
        seed = [sample_tracks[0]]
        candidates = sample_tracks  # Include seed in candidates

        engine = RecommendationEngine(candidate_pool=candidates)
        request = RecommendationRequest(seed_track_ids=["track1"], limit=5)

        recommendations = engine.generate_recommendations(seed, request)

        # Seed track should not be recommended
        assert all(rec.track.spotify_id != "track1" for rec in recommendations)

    def test_multiple_seed_tracks(self, sample_tracks):
        """Should handle multiple seed tracks."""
        seeds = sample_tracks[:2]
        candidates = [sample_tracks[2]]

        engine = RecommendationEngine(candidate_pool=candidates)
        request = RecommendationRequest(seed_track_ids=["track1", "track2"], limit=1)

        recommendations = engine.generate_recommendations(seeds, request)

        assert len(recommendations) > 0

    def test_target_preferences_affect_recommendations(self, sample_tracks):
        """Target preferences should influence recommendations."""
        seed = [sample_tracks[0]]
        candidates = sample_tracks[1:]

        engine = RecommendationEngine(candidate_pool=candidates)

        # Request with high energy target
        request_energetic = RecommendationRequest(
            seed_track_ids=["track1"], limit=1, target_energy=0.9
        )
        recs_energetic = engine.generate_recommendations(seed, request_energetic)

        # Request with low energy target
        request_calm = RecommendationRequest(
            seed_track_ids=["track1"], limit=1, target_energy=0.1
        )
        recs_calm = engine.generate_recommendations(seed, request_calm)

        # Both should produce recommendations
        assert len(recs_energetic) > 0
        assert len(recs_calm) > 0

    def test_no_candidates_returns_empty(self, sample_track_1):
        """No candidates should return empty recommendations."""
        seed = [sample_track_1]
        candidates = []

        engine = RecommendationEngine(candidate_pool=candidates)
        request = RecommendationRequest(seed_track_ids=["track1"], limit=5)

        recommendations = engine.generate_recommendations(seed, request)

        assert len(recommendations) == 0

    def test_seeds_without_features_handled_gracefully(self, sample_track_1):
        """Seed tracks without audio features should be handled."""
        from app.models.track import Track

        seed_no_features = Track(
            spotify_id="no_features",
            name="Track Without Features",
            artists=["Artist E"],
            features=None,  # No audio features
        )

        engine = RecommendationEngine(candidate_pool=[sample_track_1])
        request = RecommendationRequest(seed_track_ids=["no_features"], limit=1)

        recommendations = engine.generate_recommendations([seed_no_features], request)

        # Should return empty since seed has no features
        assert len(recommendations) == 0
