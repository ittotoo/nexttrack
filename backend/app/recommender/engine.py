
from typing import List, Tuple
import logging
import random

from app.models.track import Track
from app.models.request import RecommendationRequest, RecommendationItem
from app.recommender.similarity import (
    calculate_cosine_similarity,
    calculate_average_vector,
    calculate_diversity_score,
    apply_target_preferences,
)

logger = logging.getLogger(__name__)


class RecommendationEngine:

    def __init__(self, candidate_pool: List[Track] = None):
       
        self.candidate_pool = candidate_pool or []
        logger.info(f"RecommendationEngine initialized with {len(self.candidate_pool)} candidates")

    def generate_recommendations(
        self,
        seed_tracks: List[Track],
        request: RecommendationRequest,
    ) -> List[RecommendationItem]:
        
        # Validate seed tracks have audio features
        valid_seeds = [t for t in seed_tracks if t.features is not None]
        if not valid_seeds:
            logger.warning("No valid seed tracks with audio features")
            return []

        # Extract feature vectors from seed tracks
        seed_vectors = [track.features.to_feature_vector() for track in valid_seeds]
        logger.info(f"Extracted features from {len(seed_vectors)} seed tracks")

        # Create target profile (average of seed tracks)
        target_profile = calculate_average_vector(seed_vectors)

        # Apply user preference adjustments
        target_profile = apply_target_preferences(
            target_profile,
            target_energy=request.target_energy,
            target_valence=request.target_valence,
            target_danceability=request.target_danceability,
        )

        # Score all candidate tracks
        candidates_with_scores = self._score_candidates(
            target_profile=target_profile,
            candidates=self.candidate_pool,
            diversity_weight=request.diversity_weight,
        )

        # Filter out seed tracks from recommendations
        seed_ids = {track.spotify_id for track in seed_tracks}
        candidates_with_scores = [
            (track, score, explanation)
            for track, score, explanation in candidates_with_scores
            if track.spotify_id not in seed_ids
        ]

        # Select top-K with diversity
        recommendations = self._select_top_k_diverse(
            candidates_with_scores,
            k=request.limit,
            diversity_weight=request.diversity_weight,
        )

        # Create RecommendationItem objects
        items = [
            RecommendationItem(
                track=track,
                similarity_score=score,
                explanation=explanation,
            )
            for track, score, explanation in recommendations
        ]

        logger.info(f"Generated {len(items)} recommendations")
        return items

    def _score_candidates(
        self,
        target_profile: List[float],
        candidates: List[Track],
        diversity_weight: float,
    ) -> List[Tuple[Track, float, str]]:
        
        scored = []

        for track in candidates:
            if not track.features:
                continue  # Skip tracks without audio features

            # Calculate similarity to target profile
            candidate_vector = track.features.to_feature_vector()
            similarity = calculate_cosine_similarity(candidate_vector, target_profile)

            # Generate explanation
            explanation = self._generate_explanation(track, target_profile)

            scored.append((track, similarity, explanation))

        # Sort by similarity (descending)
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored

    def _select_top_k_diverse(
        self,
        scored_candidates: List[Tuple[Track, float, str]],
        k: int,
        diversity_weight: float,
    ) -> List[Tuple[Track, float, str]]:
        
        if diversity_weight == 0.0:
            # Pure similarity-based ranking
            return scored_candidates[:k]

        selected = []
        remaining = scored_candidates.copy()

        while len(selected) < k and remaining:
            if not selected:
                # First item: select highest similarity
                selected.append(remaining.pop(0))
            else:
                # Subsequent items: balance similarity and diversity
                selected_vectors = [
                    track.features.to_feature_vector() for track, _, _ in selected
                ]

                # Rescore remaining candidates with diversity
                rescored = []
                for track, similarity, explanation in remaining:
                    candidate_vector = track.features.to_feature_vector()
                    diversity = calculate_diversity_score(candidate_vector, selected_vectors)

                    # MMR score
                    mmr_score = (1 - diversity_weight) * similarity + diversity_weight * diversity

                    rescored.append((track, similarity, explanation, mmr_score))

                # Select best MMR score
                rescored.sort(key=lambda x: x[3], reverse=True)
                best = rescored[0]
                selected.append((best[0], best[1], best[2]))

                # Remove from remaining
                remaining = [(t, s, e) for t, s, e in remaining if t.spotify_id != best[0].spotify_id]

        return selected

    def _generate_explanation(self, track: Track, target_profile: List[float]) -> str:
        
        if not track.features:
            return "Recommended based on overall similarity"

        # Perceptually meaningful features with their vector indices
        # Ordered by musical salience (energy and valence are primary
        # dimensions of musical emotion per Russell, 1980)
        meaningful_features = [
            ("energy", 2),
            ("valence", 6),
            ("danceability", 1),
            ("acousticness", 0),
            ("tempo", 7),
        ]

        candidate_vector = track.features.to_feature_vector()

        # Score each meaningful feature by how closely it matches
        feature_scores = []
        for name, idx in meaningful_features:
            diff = abs(candidate_vector[idx] - target_profile[idx])
            feature_scores.append((name, diff, candidate_vector[idx]))

        # Sort by smallest difference (best match)
        feature_scores.sort(key=lambda x: x[1])

        # Pick top 2 matching meaningful features
        top_features = feature_scores[:2]

        # Create explanation
        explanations = []
        for name, diff, value in top_features:
            if name == "energy":
                if value > 0.7:
                    explanations.append("high energy")
                elif value < 0.3:
                    explanations.append("calm vibe")
                else:
                    explanations.append("moderate energy")
            elif name == "valence":
                if value > 0.6:
                    explanations.append("positive mood")
                elif value < 0.4:
                    explanations.append("melancholic feel")
                else:
                    explanations.append("balanced mood")
            elif name == "danceability":
                if value > 0.7:
                    explanations.append("highly danceable")
                elif value < 0.3:
                    explanations.append("low danceability")
                else:
                    explanations.append("moderate groove")
            elif name == "acousticness":
                if value > 0.6:
                    explanations.append("acoustic sound")
                elif value < 0.2:
                    explanations.append("electronic/produced sound")
                else:
                    explanations.append("mixed acoustic quality")
            elif name == "tempo":
                if value > 0.6:  # >120 BPM normalised
                    explanations.append("upbeat tempo")
                elif value < 0.4:  # <80 BPM normalised
                    explanations.append("slow tempo")
                else:
                    explanations.append("moderate tempo")

        if not explanations:
            explanations = [f"similar {top_features[0][0]}"]

        return f"Matches your taste: {', '.join(explanations)}"
