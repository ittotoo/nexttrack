"""Hybrid recommendation engine combining three weighted components."""

from typing import List, Tuple, Dict
import logging

from app.models.track import Track
from app.models.request import RecommendationRequest, RecommendationItem
from app.recommender.similarity import (
    calculate_cosine_similarity,
    calculate_average_vector,
    calculate_diversity_score,
    apply_target_preferences,
)
from app.recommender.knowledge_graph import KnowledgeGraphScorer
from app.recommender.popularity import PopularityScorer

logger = logging.getLogger(__name__)

CONTENT_WEIGHT = 0.4
KNOWLEDGE_WEIGHT = 0.3
POPULARITY_WEIGHT = 0.3


class HybridRecommendationEngine:
    """Combine content, graph, and popularity signals."""

    def __init__(self, candidate_pool: List[Track], db=None):
        
        self.candidate_pool = candidate_pool or []
        self.kg_scorer = KnowledgeGraphScorer(db) if db else None
        self.pop_scorer = PopularityScorer()
        logger.info(
            f"HybridRecommendationEngine initialised with "
            f"{len(self.candidate_pool)} candidates"
        )

    def generate_recommendations(
        self,
        seed_tracks: List[Track],
        request: RecommendationRequest,
    ) -> List[RecommendationItem]:
        """Build a ranked list of recommendations."""
        
        valid_seeds = [t for t in seed_tracks if t.features is not None]
        if not valid_seeds:
            logger.warning("No valid seed tracks with audio features")
            return []

        # Content-Based Filtering (40%)
        content_scores = self._score_content(valid_seeds, request)

        # Knowledge Graph (30%)
        kg_scores = self._score_knowledge_graph(seed_tracks)

        # Popularity (30%)
        pop_scores = self._score_popularity(seed_tracks)

        
        hybrid_scored = self._combine_scores(
            content_scores, kg_scores, pop_scores
        )

        # Filter out seed tracks
        seed_ids = {t.spotify_id for t in seed_tracks}
        hybrid_scored = [
            item for item in hybrid_scored
            if item[0].spotify_id not in seed_ids
        ]

        recommendations = self._select_top_k_diverse(
            hybrid_scored,
            k=request.limit,
            diversity_weight=request.diversity_weight,
        )

        # Build RecommendationItem objects
        items = [
            RecommendationItem(
                track=track,
                similarity_score=round(hybrid_score, 4),
                explanation=explanation,
                content_score=round(scores['content'], 4),
                knowledge_score=round(scores['knowledge'], 4),
                popularity_score=round(scores['popularity'], 4),
            )
            for track, hybrid_score, explanation, scores in recommendations
        ]

        logger.info(f"Generated {len(items)} hybrid recommendations")

        del content_scores, kg_scores, pop_scores, hybrid_scored, recommendations

        return items

    def _score_content(
        self,
        seed_tracks: List[Track],
        request: RecommendationRequest,
    ) -> Dict[str, Tuple[float, str]]:
        """Score candidates from audio features."""
        seed_vectors = [t.features.to_feature_vector() for t in seed_tracks]
        target_profile = calculate_average_vector(seed_vectors)

        target_profile = apply_target_preferences(
            target_profile,
            target_energy=request.target_energy,
            target_valence=request.target_valence,
            target_danceability=request.target_danceability,
        )

        scores = {}
        for track in self.candidate_pool:
            if not track.features:
                scores[track.spotify_id] = (0.0, "")
                continue

            candidate_vector = track.features.to_feature_vector()
            similarity = calculate_cosine_similarity(candidate_vector, target_profile)
            explanation = self._content_explanation(track, target_profile)
            scores[track.spotify_id] = (similarity, explanation)

        return scores

    def _score_knowledge_graph(
        self, seed_tracks: List[Track]
    ) -> Dict[str, Tuple[float, str]]:
        """Score candidates using knowledge-graph signals.   """
        if not self.kg_scorer:
            return {t.spotify_id: (0.0, "") for t in self.candidate_pool}

        kg_results = self.kg_scorer.score_candidates(seed_tracks, self.candidate_pool)

        scores = {}
        for track, score, explanation in kg_results:
            scores[track.spotify_id] = (score, explanation)

        return scores

    def _score_popularity(
        self, seed_tracks: List[Track]
    ) -> Dict[str, Tuple[float, str]]:
        """Score candidates using popularity. """
        pop_results = self.pop_scorer.score_candidates(seed_tracks, self.candidate_pool)

        scores = {}
        for track, score, explanation in pop_results:
            scores[track.spotify_id] = (score, explanation)

        return scores

    def _combine_scores(
        self,
        content_scores: Dict[str, Tuple[float, str]],
        kg_scores: Dict[str, Tuple[float, str]],
        pop_scores: Dict[str, Tuple[float, str]],
    ) -> List[Tuple[Track, float, str, Dict[str, float]]]:
        """Merge all component scores into one ranking. """
        combined = []

        for track in self.candidate_pool:
            sid = track.spotify_id

            c_score, c_expl = content_scores.get(sid, (0.0, ""))
            k_score, k_expl = kg_scores.get(sid, (0.0, ""))
            p_score, p_expl = pop_scores.get(sid, (0.0, ""))

            hybrid = (
                CONTENT_WEIGHT * c_score
                + KNOWLEDGE_WEIGHT * k_score
                + POPULARITY_WEIGHT * p_score
            )

            explanation = self._combine_explanations(c_expl, k_expl, p_expl)

            component_scores = {
                'content': c_score,
                'knowledge': k_score,
                'popularity': p_score,
            }

            combined.append((track, hybrid, explanation, component_scores))

        combined.sort(key=lambda x: x[1], reverse=True)
        return combined

    def _select_top_k_diverse(
        self,
        scored_candidates: List[Tuple[Track, float, str, Dict[str, float]]],
        k: int,
        diversity_weight: float,
    ) -> List[Tuple[Track, float, str, Dict[str, float]]]:
        """Pick top results, with optional diversity re-ranking. """
        if diversity_weight == 0.0:
            return scored_candidates[:k]

        selected = []
        remaining = scored_candidates.copy()

        while len(selected) < k and remaining:
            if not selected:
                selected.append(remaining.pop(0))
            else:
                selected_vectors = [
                    t.features.to_feature_vector()
                    for t, _, _, _ in selected
                    if t.features
                ]

                rescored = []
                for track, hybrid, explanation, scores in remaining:
                    if not track.features:
                        rescored.append((track, hybrid, explanation, scores, hybrid))
                        continue

                    candidate_vector = track.features.to_feature_vector()
                    diversity = calculate_diversity_score(
                        candidate_vector, selected_vectors
                    )
                    mmr = (1 - diversity_weight) * hybrid + diversity_weight * diversity
                    rescored.append((track, hybrid, explanation, scores, mmr))

                rescored.sort(key=lambda x: x[4], reverse=True)
                best = rescored[0]
                selected.append((best[0], best[1], best[2], best[3]))
                remaining = [
                    (t, h, e, s) for t, h, e, s in remaining
                    if t.spotify_id != best[0].spotify_id
                ]

        return selected

    def _content_explanation(
        self, track: Track, target_profile: List[float]
    ) -> str:
        """Return a short content-based explanation. """
        if not track.features:
            return ""

        meaningful_features = [
            ("energy", 2),
            ("valence", 6),
            ("danceability", 1),
            ("acousticness", 0),
            ("tempo", 7),
        ]

        candidate_vector = track.features.to_feature_vector()

        feature_scores = []
        for name, idx in meaningful_features:
            diff = abs(candidate_vector[idx] - target_profile[idx])
            feature_scores.append((name, diff, candidate_vector[idx]))

        feature_scores.sort(key=lambda x: x[1])
        top = feature_scores[0]

        labels = {
            "energy": lambda v: "high energy" if v > 0.7 else "calm vibe" if v < 0.3 else "moderate energy",
            "valence": lambda v: "positive mood" if v > 0.6 else "melancholic feel" if v < 0.4 else "balanced mood",
            "danceability": lambda v: "highly danceable" if v > 0.7 else "low danceability" if v < 0.3 else "moderate groove",
            "acousticness": lambda v: "acoustic sound" if v > 0.6 else "electronic sound" if v < 0.2 else "mixed acoustic",
            "tempo": lambda v: "upbeat tempo" if v > 0.6 else "slow tempo" if v < 0.4 else "moderate tempo",
        }

        return labels[top[0]](top[2])

    def _combine_explanations(
        self, content_expl: str, kg_expl: str, pop_expl: str
    ) -> str:
        """Merge non-empty explanations into one sentence. """
        parts = []

        if content_expl:
            parts.append(content_expl)
        if kg_expl:
            parts.append(kg_expl)
        if pop_expl:
            parts.append(pop_expl)

        if not parts:
            return "Recommended based on overall similarity"

        return "Matches your taste: " + ", ".join(parts)
