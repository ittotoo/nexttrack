"""Popularity-based scoring."""

from typing import List, Tuple
import logging

from app.models.track import Track

logger = logging.getLogger(__name__)

ALIGNMENT_WEIGHT = 0.6
RAW_POPULARITY_WEIGHT = 0.4


class PopularityScorer:
    """Score tracks based on how their popularity compares to the seeds.  """

    def score_candidates(
        self,
        seed_tracks: List[Track],
        candidates: List[Track],
    ) -> List[Tuple[Track, float, str]]:
        """Return popularity scores for candidates."""

        # average popularity of the seeds (fallback to mid if missing)
        seed_pops = [
            t.popularity for t in seed_tracks if t.popularity is not None
        ]
        seed_mean_pop = sum(seed_pops) / len(seed_pops) if seed_pops else 50.0

        logger.info(f"Seed mean popularity: {seed_mean_pop:.1f}")

        results = []
        for track in candidates:
            pop = track.popularity if track.popularity is not None else 0

            #  how close are we to the seed "range"
            alignment = 1.0 - abs(pop - seed_mean_pop) / 100.0

            # raw popularity signal
            raw_pop = pop / 100.0

            score = ALIGNMENT_WEIGHT * alignment + RAW_POPULARITY_WEIGHT * raw_pop

            explanation = self._generate_explanation(pop, seed_mean_pop)
            results.append((track, score, explanation))

        return results

    def _generate_explanation(
        self, popularity: int, seed_mean_pop: float
    ) -> str:
        """Small explanation string (used in UI/debug).  """
        diff = abs(popularity - seed_mean_pop)

        if diff <= 10:
            if popularity >= 70:
                return "popular track in your range"
            elif popularity <= 30:
                return "hidden gem matching your taste"
            else:
                return "similar popularity range"
        elif popularity >= 80:
            return "widely popular track"
        elif popularity <= 20:
            return "deep cut discovery"
        else:
            return ""
