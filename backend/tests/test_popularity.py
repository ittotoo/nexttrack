"""Tests for popularity scorer component."""

import pytest
from app.recommender.popularity import PopularityScorer
from app.models.track import Track, AudioFeatures


def _make_track(spotify_id, popularity, genre="pop"):
    """Helper to create a minimal track with popularity."""
    return Track(
        spotify_id=spotify_id,
        name=f"Track {spotify_id}",
        artists=["Test Artist"],
        genre=genre,
        popularity=popularity,
        features=AudioFeatures(
            acousticness=0.5, danceability=0.5, energy=0.5,
            instrumentalness=0.0, liveness=0.1, loudness=-8.0,
            speechiness=0.05, valence=0.5, tempo=120.0,
            time_signature=4, key=0, mode=1, duration_ms=200000,
        ),
    )


class TestPopularityScorer:
    """Tests for the PopularityScorer class."""

    def test_exact_popularity_match_scores_high(self):
        """Candidate with same popularity as seed mean should score highest."""
        scorer = PopularityScorer()
        seed = _make_track("seed", 80)
        exact_match = _make_track("exact", 80)
        distant = _make_track("distant", 20)

        results = scorer.score_candidates(
            seed_tracks=[seed],
            candidates=[exact_match, distant],
        )

        score_exact = next(s for t, s, e in results if t.spotify_id == "exact")
        score_distant = next(s for t, s, e in results if t.spotify_id == "distant")
        assert score_exact > score_distant

    def test_alignment_score_for_exact_match(self):
        """Perfect alignment should give alignment component = 1.0."""
        scorer = PopularityScorer()
        seed = _make_track("seed", 50)
        candidate = _make_track("cand", 50)

        results = scorer.score_candidates([seed], [candidate])
        _, score, _ = results[0]

       
        assert score == pytest.approx(0.8)

    def test_low_popularity_distant_from_high_seed(self):
        """Low popularity candidate far from high popularity seed scores low."""
        scorer = PopularityScorer()
        seed = _make_track("seed", 90)
        candidate = _make_track("cand", 10)

        results = scorer.score_candidates([seed], [candidate])
        _, score, _ = results[0]

        
        assert score == pytest.approx(0.16)

    def test_scores_always_between_zero_and_one(self):
        """All popularity scores must be in [0, 1]."""
        scorer = PopularityScorer()
        seed = _make_track("seed", 50)
        candidates = [_make_track(f"c{i}", pop) for i, pop in enumerate([0, 25, 50, 75, 100])]

        results = scorer.score_candidates([seed], candidates)
        for _, score, _ in results:
            assert 0.0 <= score <= 1.0

    def test_multiple_seeds_averages_popularity(self):
        """Multiple seed tracks should use average popularity."""
        scorer = PopularityScorer()
        seeds = [_make_track("s1", 80), _make_track("s2", 40)]
        # Mean = 60
        candidate = _make_track("cand", 60)

        results = scorer.score_candidates(seeds, [candidate])
        _, score, _ = results[0]

       
        assert score == pytest.approx(0.84)

    def test_explanation_for_popular_in_range(self):
        """Popular track near seed range should get appropriate explanation."""
        scorer = PopularityScorer()
        seed = _make_track("seed", 75)
        candidate = _make_track("cand", 80)

        results = scorer.score_candidates([seed], [candidate])
        _, _, explanation = results[0]
        assert "popular" in explanation.lower() or "range" in explanation.lower()

    def test_explanation_for_hidden_gem(self):
        """Low popularity track matching seed range should be called hidden gem."""
        scorer = PopularityScorer()
        seed = _make_track("seed", 25)
        candidate = _make_track("cand", 22)

        results = scorer.score_candidates([seed], [candidate])
        _, _, explanation = results[0]
        assert "hidden gem" in explanation.lower()

    def test_none_popularity_treated_as_zero(self):
        """Track with None popularity should be treated as 0."""
        scorer = PopularityScorer()
        seed = _make_track("seed", 50)
        candidate = Track(
            spotify_id="none_pop",
            name="No Pop",
            artists=["Artist"],
            popularity=None,
            features=AudioFeatures(
                acousticness=0.5, danceability=0.5, energy=0.5,
                instrumentalness=0.0, liveness=0.1, loudness=-8.0,
                speechiness=0.05, valence=0.5, tempo=120.0,
                time_signature=4, key=0, mode=1, duration_ms=200000,
            ),
        )

        results = scorer.score_candidates([seed], [candidate])
        _, score, _ = results[0]
        assert 0.0 <= score <= 1.0
