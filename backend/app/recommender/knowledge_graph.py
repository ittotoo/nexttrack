"""Knowledge-graph scoring for hybrid recommendations."""

from typing import List, Dict, Set, Tuple
import logging

from app.models.track import Track
from app.recommender.genre_taxonomy import get_genre_similarity

logger = logging.getLogger(__name__)


DECAY_FACTOR = 0.5
ARTIST_WEIGHT = 0.6
GENRE_WEIGHT = 0.4


class KnowledgeGraphScorer:
    """Score candidates using artist links and genre similarity."""

    def __init__(self, db):
        self.db = db

    def score_candidates(
        self,
        seed_tracks: List[Track],
        candidates: List[Track],
    ) -> List[Tuple[Track, float, str]]:
        """Return KG scores for candidate tracks."""

        # Get seed artist IDs
        seed_spotify_ids = [t.spotify_id for t in seed_tracks]
        seed_artist_mapping = self.db.get_artist_ids_for_tracks(seed_spotify_ids)
        seed_artist_ids = set()
        for ids in seed_artist_mapping.values():
            seed_artist_ids.update(ids)

        if not seed_artist_ids:
            logger.warning("No artist IDs found for seed tracks")
            return [(t, 0.0, "") for t in candidates]

        # Get seed genres
        seed_genres = set()
        for t in seed_tracks:
            if t.genre:
                seed_genres.add(t.genre)

        # BFS from seed artists to find reachable artists with decay
        reachable = self._bfs_with_decay(list(seed_artist_ids))

        # Get candidatte artist IDs in batch
        candidate_db_ids = [t.db_id for t in candidates if t.db_id is not None]
        candidate_artist_mapping = self.db.get_candidate_artist_ids(candidate_db_ids)

        # Score each candiddate
        results = []
        for track in candidates:
            artist_score = self._score_artist_proximity(
                track, candidate_artist_mapping, seed_artist_ids, reachable
            )
            genre_score = self._score_genre_proximity(track, seed_genres)

            kg_score = ARTIST_WEIGHT * artist_score + GENRE_WEIGHT * genre_score
            explanation = self._generate_explanation(
                track, artist_score, genre_score, seed_genres
            )

            results.append((track, kg_score, explanation))

        return results

    def _bfs_with_decay(self, seed_artist_ids: List[int]) -> Dict[int, float]:
        """Run BFS and apply decay per hop. """
        bfs_results = self.db.get_artist_relationships_bfs(seed_artist_ids)

        # Apply exponential decay: score = weight * 0.5^depth
        reachable: Dict[int, float] = {}
        for row in bfs_results:
            artist_id = row['artist_id']
            depth = row['depth']
            weight = row['weight']

            decayed_score = weight * (DECAY_FACTOR ** depth)

            # Keep highest score for each artist
            if artist_id not in reachable or decayed_score > reachable[artist_id]:
                reachable[artist_id] = decayed_score

        return reachable

    def _score_artist_proximity(
        self,
        track: Track,
        candidate_artist_mapping: Dict[int, List[int]],
        seed_artist_ids: Set[int],
        reachable: Dict[int, float],
    ) -> float:
        """Best artist proximity for this track."""
        if track.db_id is None:
            return 0.0

        artist_ids = candidate_artist_mapping.get(track.db_id, [])
        if not artist_ids:
            return 0.0

        best_score = 0.0
        for aid in artist_ids:
            if aid in seed_artist_ids:
                best_score = max(best_score, 1.0)  # Same artist = max score
            elif aid in reachable:
                best_score = max(best_score, reachable[aid])

        return best_score

    def _score_genre_proximity(
        self, track: Track, seed_genres: Set[str]
    ) -> float:
        """Best genre similarity against seeds. """
        if not track.genre or not seed_genres:
            return 0.0

        # Best similarity between candidate genre and any seed genre
        best_sim = 0.0
        for sg in seed_genres:
            sim = get_genre_similarity(track.genre, sg)
            best_sim = max(best_sim, sim)

        return best_sim

    def _generate_explanation(
        self,
        track: Track,
        artist_score: float,
        genre_score: float,
        seed_genres: Set[str],
    ) -> str:
        """Short explanation string for UI/debug.   """
        parts = []

        if artist_score >= 0.8:
            parts.append("shares artist connections with your seeds")
        elif artist_score >= 0.3:
            parts.append("related artist network")

        if genre_score >= 0.8:
            parts.append(f"same genre ({track.genre})")
        elif genre_score >= 0.4:
            parts.append(f"similar genre ({track.genre})")

        if not parts:
            return ""

        return ", ".join(parts)
