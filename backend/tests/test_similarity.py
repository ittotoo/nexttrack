"""Tests for similarity calculation functions."""

import pytest
from app.recommender.similarity import (
    calculate_cosine_similarity,
    calculate_average_vector,
    calculate_diversity_score,
    apply_target_preferences,
)


class TestCosineSimilarity:
    """Tests for cosine similarity calculation."""

    def test_identical_vectors(self):
        """Identical vectors should have similarity of 1.0."""
        vector = [0.5, 0.5, 0.5, 0.5]
        similarity = calculate_cosine_similarity(vector, vector)
        assert similarity == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity close to 0."""
        v1 = [1.0, 0.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0, 0.0]
        similarity = calculate_cosine_similarity(v1, v2)
        assert similarity == pytest.approx(0.0)

    def test_similar_vectors(self):
        """Similar vectors should have high similarity."""
        v1 = [0.8, 0.9, 0.7, 0.6]
        v2 = [0.75, 0.85, 0.72, 0.65]
        similarity = calculate_cosine_similarity(v1, v2)
        assert similarity > 0.9

    def test_opposite_vectors(self):
        """Opposite vectors should have low similarity (normalized to 0+)."""
        v1 = [1.0, 1.0, 1.0, 1.0]
        v2 = [0.0, 0.0, 0.0, 0.0]
        similarity = calculate_cosine_similarity(v1, v2)
        assert similarity >= 0.0


class TestAverageVector:
    """Tests for average vector calculation."""

    def test_single_vector(self):
        """Average of single vector should be the vector itself."""
        vector = [0.5, 0.6, 0.7, 0.8]
        avg = calculate_average_vector([vector])
        assert avg == pytest.approx(vector)

    def test_two_vectors(self):
        """Average of two vectors should be their mean."""
        v1 = [0.4, 0.6, 0.8, 1.0]
        v2 = [0.6, 0.4, 0.2, 0.0]
        expected = [0.5, 0.5, 0.5, 0.5]
        avg = calculate_average_vector([v1, v2])
        assert avg == pytest.approx(expected)

    def test_multiple_vectors(self):
        """Average of multiple vectors."""
        vectors = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
        expected = [1 / 3, 1 / 3, 1 / 3]
        avg = calculate_average_vector(vectors)
        assert avg == pytest.approx(expected, abs=0.01)

    def test_empty_list(self):
        """Empty list should return empty list."""
        avg = calculate_average_vector([])
        assert avg == []


class TestDiversityScore:
    """Tests for diversity score calculation."""

    def test_first_track_is_maximally_diverse(self):
        """First track should have diversity score of 1.0."""
        candidate = [0.5, 0.5, 0.5]
        diversity = calculate_diversity_score(candidate, selected_vectors=[])
        assert diversity == 1.0

    def test_identical_to_selected_has_zero_diversity(self):
        """Track identical to selected should have diversity ~0."""
        candidate = [0.8, 0.6, 0.7]
        selected = [[0.8, 0.6, 0.7]]
        diversity = calculate_diversity_score(candidate, selected)
        assert diversity == pytest.approx(0.0, abs=0.1)

    def test_different_from_selected_has_high_diversity(self):
        """Track very different from selected should have high diversity."""
        candidate = [1.0, 0.0, 0.0]
        selected = [[0.0, 1.0, 0.0]]
        diversity = calculate_diversity_score(candidate, selected)
        assert diversity > 0.8


class TestApplyTargetPreferences:
    """Tests for target preference application."""

    def test_no_preferences_returns_original(self):
        """No preferences should return original vector."""
        vector = [0.5, 0.6, 0.7, 0.4, 0.3, 0.2, 0.8, 0.5]
        result = apply_target_preferences(vector)
        assert result == vector

    def test_target_energy_adjusts_energy_index(self):
        """Target energy should adjust energy component (index 2)."""
        vector = [0.5, 0.6, 0.4, 0.4, 0.3, 0.2, 0.8, 0.5]
        result = apply_target_preferences(vector, target_energy=0.8)
        # Energy at index 2 should be blend of 0.4 and 0.8 = 0.6
        assert result[2] == pytest.approx(0.6)

    def test_target_valence_adjusts_valence_index(self):
        """Target valence should adjust valence component (index 6)."""
        vector = [0.5, 0.6, 0.4, 0.4, 0.3, 0.2, 0.4, 0.5]
        result = apply_target_preferences(vector, target_valence=0.8)
        # Valence at index 6 should be blend of 0.4 and 0.8 = 0.6
        assert result[6] == pytest.approx(0.6)

    def test_target_danceability_adjusts_danceability_index(self):
        """Target danceability should adjust danceability component (index 1)."""
        vector = [0.5, 0.4, 0.4, 0.4, 0.3, 0.2, 0.8, 0.5]
        result = apply_target_preferences(vector, target_danceability=0.8)
        # Danceability at index 1 should be blend of 0.4 and 0.8 = 0.6
        assert result[1] == pytest.approx(0.6)

    def test_multiple_preferences(self):
        """Multiple preferences should all be applied."""
        vector = [0.5, 0.2, 0.2, 0.4, 0.3, 0.2, 0.2, 0.5]
        result = apply_target_preferences(
            vector, target_energy=0.8, target_valence=0.8, target_danceability=0.8
        )
        assert result[1] == pytest.approx(0.5)  # Danceability
        assert result[2] == pytest.approx(0.5)  # Energy
        assert result[6] == pytest.approx(0.5)  # Valence
