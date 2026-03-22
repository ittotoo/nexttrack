"""Similarity calculation functions for content-based filtering."""

from typing import List

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def calculate_cosine_similarity(vector1: List[float], vector2: List[float]) -> float:
    """Return cosine similarity for two vectors.
    Formula: similarity = (A · B) / (||A|| × ||B||)
    """
    v1 = np.array(vector1).reshape(1, -1)
    v2 = np.array(vector2).reshape(1, -1)

    similarity = cosine_similarity(v1, v2)[0][0]

    # Clamp negatives to 0 since we only care about useful similarity here.
    # In practice, audio features rarely produce negative similarity
    return float(max(0.0, similarity))


def calculate_average_vector(vectors: List[List[float]]) -> List[float]:
    """Return the mean vector for a list of vectors."""
    if not vectors:
        return []

    vectors_array = np.array(vectors)
    avg_vector = np.mean(vectors_array, axis=0)
    return avg_vector.tolist()


def calculate_diversity_score(
    candidate_vector: List[float],
    selected_vectors: List[List[float]],
) -> float:
    """Score how different a candidate is from already selected items.  """

    if not selected_vectors:
        return 1.0  # First track is maximally diverse

    # Feature values are normalized to [0, 1], so this is the largest possible
    # Euclidean distance for a vector of this size.
    n_dims = len(candidate_vector)
    max_dist = np.sqrt(n_dims)

    distances = []
    for selected in selected_vectors:
        dist = np.linalg.norm(np.array(candidate_vector) - np.array(selected))
        # Normalise to [0, 1]
        distances.append(dist / max_dist)

    return float(np.mean(distances))


def apply_target_preferences(
    vector: List[float],
    target_energy: float = None,
    target_valence: float = None,
    target_danceability: float = None,
) -> List[float]:
    """Nudge a feature vector toward requested target values.

    Vector layout:
    [acousticness, danceability, energy, instrumentalness,
     liveness, speechiness, valence, tempo_normalized]
    """
    adjusted = vector.copy()

    # Map targets to indices in feature vector
    if target_danceability is not None:
        adjusted[1] = (adjusted[1] + target_danceability) / 2  # Blend with target

    if target_energy is not None:
        adjusted[2] = (adjusted[2] + target_energy) / 2

    if target_valence is not None:
        adjusted[6] = (adjusted[6] + target_valence) / 2

    return adjusted
