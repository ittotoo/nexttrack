"""Tests for knowledge graph scorer component."""

import pytest
from unittest.mock import MagicMock

from app.recommender.knowledge_graph import KnowledgeGraphScorer, DECAY_FACTOR
from app.recommender.genre_taxonomy import get_genre_similarity, get_supergenre


class TestGenreTaxonomy:
    """Tests for genre taxonomy and similarity calculation."""

    def test_same_genre_returns_one(self):
        assert get_genre_similarity("rock", "rock") == 1.0

    def test_same_supergenre_returns_half(self):
        # alt-rock and grunge are both in ROCK supergenre
        assert get_genre_similarity("alt-rock", "grunge") == 0.5

    def test_related_supergenres_returns_quarter(self):
        # rock (ROCK) and metal (METAL) are related supergenres
        assert get_genre_similarity("rock", "metal") == 0.25

    def test_unrelated_supergenres_returns_zero(self):
        # classical and hip-hop are unrelated
        assert get_genre_similarity("classical", "hip-hop") == 0.0

    def test_unknown_genre_returns_zero(self):
        assert get_genre_similarity("nonexistent", "rock") == 0.0

    def test_all_genres_have_supergenre(self):
        """Every genre in the taxonomy should map to a supergenre."""
        from app.recommender.genre_taxonomy import GENRE_TO_SUPERGENRE
        for genre in GENRE_TO_SUPERGENRE:
            assert get_supergenre(genre) is not None

    def test_symmetry(self):
        """Genre similarity should be symmetric."""
        assert get_genre_similarity("rock", "metal") == get_genre_similarity("metal", "rock")


class TestKnowledgeGraphScorer:
    """Tests for the KnowledgeGraphScorer class."""

    def _make_scorer(self, bfs_results, artist_mapping, candidate_mapping):
        """Helper to create a scorer with mocked database."""
        mock_db = MagicMock()
        mock_db.get_artist_ids_for_tracks.return_value = artist_mapping
        mock_db.get_artist_relationships_bfs.return_value = bfs_results
        mock_db.get_candidate_artist_ids.return_value = candidate_mapping
        return KnowledgeGraphScorer(mock_db)

    def test_direct_collaborator_scores_high(
        self, sample_track_1, sample_track_2, sample_track_3,
        mock_artist_mapping, mock_bfs_results, mock_candidate_artist_mapping
    ):
        """Track by a direct collaborator should score higher than distant artist."""
        scorer = self._make_scorer(
            mock_bfs_results, mock_artist_mapping, mock_candidate_artist_mapping
        )

        results = scorer.score_candidates(
            seed_tracks=[sample_track_1],
            candidates=[sample_track_2, sample_track_3],
        )

        # Track 2 (artist 20, depth 1) should score higher than Track 3 (artist 30, depth 2)
        score_track2 = next(s for t, s, e in results if t.spotify_id == "track2")
        score_track3 = next(s for t, s, e in results if t.spotify_id == "track3")
        assert score_track2 > score_track3

    def test_bfs_decay_halves_per_depth(self, mock_bfs_results):
        
        mock_db = MagicMock()
        mock_db.get_artist_relationships_bfs.return_value = mock_bfs_results

        scorer = KnowledgeGraphScorer(mock_db)
        reachable = scorer._bfs_with_decay([10, 11])

        # Artist 20 at depth 1 with weight 1.0: 1.0 * 0.5^1 = 0.5
        assert reachable[20] == pytest.approx(0.5)

        # Artist 30 at depth 2 with weight 0.7: 0.7 * 0.5^2 = 0.175
        assert reachable[30] == pytest.approx(0.175)

    def test_no_relationships_returns_zero(
        self, sample_track_1, sample_track_2
    ):
        """Tracks with no KG connections should score 0 for artist proximity."""
        mock_db = MagicMock()
        mock_db.get_artist_ids_for_tracks.return_value = {"track1": [10]}
        mock_db.get_artist_relationships_bfs.return_value = []  # No edges
        mock_db.get_candidate_artist_ids.return_value = {2: [20]}

        scorer = KnowledgeGraphScorer(mock_db)
        results = scorer.score_candidates(
            seed_tracks=[sample_track_1],
            candidates=[sample_track_2],
        )

        _, score, _ = results[0]
        # Genre component might still contribute, but artist component is 0
        # With electronic seed and ambient candidate (related supergenres): 0.25 genre sim
        # Total: 0.6 * 0.0 + 0.4 * 0.25 = 0.1
        assert score <= 0.15

    def test_same_artist_scores_max(
        self, sample_track_1
    ):
        """A candidate by the same artist as a seed should get max artist score."""
        # Create candidate with same artist ID as seed
        candidate = sample_track_1.model_copy(
            update={"spotify_id": "track_same_artist", "db_id": 99}
        )

        mock_db = MagicMock()
        mock_db.get_artist_ids_for_tracks.return_value = {"track1": [10]}
        mock_db.get_artist_relationships_bfs.return_value = []
        mock_db.get_candidate_artist_ids.return_value = {99: [10]}  # Same artist

        scorer = KnowledgeGraphScorer(mock_db)
        results = scorer.score_candidates(
            seed_tracks=[sample_track_1],
            candidates=[candidate],
        )

        _, score, _ = results[0]
        # Artist score = 1.0 (same artist), genre = 1.0 (same genre)
        # Total: 0.6 * 1.0 + 0.4 * 1.0 = 1.0
        assert score == pytest.approx(1.0)

    def test_genre_proximity_contributes_to_score(
        self, sample_track_1, sample_track_3
    ):
        """Genre similarity should contribute to the KG score."""
        mock_db = MagicMock()
        mock_db.get_artist_ids_for_tracks.return_value = {"track1": [10]}
        mock_db.get_artist_relationships_bfs.return_value = []
        mock_db.get_candidate_artist_ids.return_value = {3: [30]}

        scorer = KnowledgeGraphScorer(mock_db)
        results = scorer.score_candidates(
            seed_tracks=[sample_track_1],  # genre=electronic
            candidates=[sample_track_3],   # genre=rock
        )

        _, score, _ = results[0]
        # electronic and rock are unrelated supergenres -> genre_sim = 0.0
        # artist not connected -> artist_score = 0.0
        assert score == pytest.approx(0.0)

    def test_scores_always_between_zero_and_one(
        self, sample_tracks, mock_artist_mapping,
        mock_bfs_results, mock_candidate_artist_mapping
    ):
        """All KG scores must be in [0, 1]."""
        scorer = self._make_scorer(
            mock_bfs_results, mock_artist_mapping, mock_candidate_artist_mapping
        )

        results = scorer.score_candidates(
            seed_tracks=[sample_tracks[0]],
            candidates=sample_tracks,
        )

        for _, score, _ in results:
            assert 0.0 <= score <= 1.0
