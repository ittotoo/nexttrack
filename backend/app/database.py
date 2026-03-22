"""Database connection and query utilities for NextTrack"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional, Dict, Any
import logging
from contextlib import contextmanager

from app.config import settings
from app.models.track import Track, AudioFeatures

logger = logging.getLogger(__name__)


class Database:
    
    def __init__(self):
        
        self.connection_params = {
            'dbname': settings.db_name,
            'user': settings.db_user,
            'password': settings.db_password,
            'host': settings.db_host,
            'port': settings.db_port
        }
        logger.info("Database configured for nexttrack")

    @contextmanager
    def get_connection(self):
        
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _row_to_track(self, row: Dict[str, Any]) -> Track:
        """Convert database row to Track object with AudioFeatures. """
        # Parse artists string into list
        artists_str = row.get('artists', '')
        artists = [a.strip() for a in artists_str.split(',')] if artists_str else []

        # Create AudioFeatures object if all required data is present
        features = None
        # Check if critical audio features exist (tempo and time_signature are required)
        if (row.get('energy') is not None and
            row.get('tempo') is not None and
            row.get('time_signature') is not None and
            row.get('duration_ms') is not None):
            features = AudioFeatures(
                acousticness=row.get('acousticness', 0.5),
                danceability=row.get('danceability', 0.5),
                energy=row['energy'],
                instrumentalness=row.get('instrumentalness', 0.0),
                liveness=row.get('liveness', 0.1),
                loudness=row.get('loudness', -10.0),
                speechiness=row.get('speechiness', 0.1),
                valence=row.get('valence', 0.5),
                tempo=row['tempo'],
                time_signature=row['time_signature'],
                key=row.get('key', -1),
                mode=row.get('mode', 1),
                duration_ms=row['duration_ms'],
            )

        # Create Track object
        return Track(
            spotify_id=row['spotify_track_id'],
            name=row['track_name'],
            artists=artists,
            album=row.get('album_name'),
            release_date=None,  # Not in database
            genre=row.get('track_genre'),
            features=features,
            preview_url=None,  # Not in database
            popularity=row.get('popularity'),
            db_id=row.get('id'),
        )

    def get_track_by_spotify_id(self, spotify_id: str) -> Optional[Track]:
        """Get complete track information by Spotify track ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT
                    spotify_track_id,
                    track_name,
                    artists,
                    album_name,
                    track_genre,
                    popularity,
                    duration_ms,
                    explicit,
                    danceability,
                    energy,
                    speechiness,
                    acousticness,
                    instrumentalness,
                    liveness,
                    valence,
                    tempo,
                    loudness,
                    key,
                    mode,
                    time_signature
                FROM v_tracks_complete
                WHERE spotify_track_id = %s
            """

            cursor.execute(query, (spotify_id,))
            result = cursor.fetchone()
            cursor.close()

            if result:
                return self._row_to_track(dict(result))
            return None

    def get_tracks_by_spotify_ids(self, spotify_ids: List[str]) -> List[Track]:
        """Get multiple tracks by Spotify IDs"""
        if not spotify_ids:
            return []

        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT
                    spotify_track_id,
                    track_name,
                    artists,
                    album_name,
                    track_genre,
                    popularity,
                    duration_ms,
                    explicit,
                    danceability,
                    energy,
                    speechiness,
                    acousticness,
                    instrumentalness,
                    liveness,
                    valence,
                    tempo,
                    loudness,
                    key,
                    mode,
                    time_signature
                FROM v_tracks_complete
                WHERE spotify_track_id = ANY(%s)
            """

            cursor.execute(query, (spotify_ids,))
            results = cursor.fetchall()
            cursor.close()

            return [self._row_to_track(dict(row)) for row in results]

    def search_tracks(self,
                     query: str = None,
                     genre: str = None,
                     min_popularity: int = 0,
                     limit: int = 50) -> List[Track]:
        """Search tracks with filters"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            where_clauses = []
            params = []

            if query:
                where_clauses.append("(track_name ILIKE %s OR artists ILIKE %s)")
                search_pattern = f"%{query}%"
                params.extend([search_pattern, search_pattern])

            if genre:
                where_clauses.append("track_genre = %s")
                params.append(genre)

            if min_popularity > 0:
                where_clauses.append("popularity >= %s")
                params.append(min_popularity)

            where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"
            params.append(limit)

            sql = f"""
                SELECT
                    spotify_track_id,
                    track_name,
                    artists,
                    album_name,
                    track_genre,
                    popularity,
                    duration_ms,
                    explicit,
                    danceability,
                    energy,
                    valence
                FROM v_tracks_complete
                WHERE {where_sql}
                ORDER BY popularity DESC
                LIMIT %s
            """

            cursor.execute(sql, params)
            results = cursor.fetchall()
            cursor.close()

            return [self._row_to_track(dict(row)) for row in results]

    def get_similar_tracks_by_features(self,
                                      seed_features: Dict[str, float],
                                      limit: int = 50,
                                      exclude_ids: List[str] = None) -> List[Track]:
        """ Find similar tracks using cosine similarity on audio features """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Build exclusion clause
            exclude_clause = ""
            if exclude_ids:
                exclude_clause = "AND t.track_id NOT IN %(exclude_ids)s"

            # Normalize tempo to 0-1 range (typical tempo: 50-200 BPM)
            seed_tempo_norm = seed_features.get('tempo', 120) / 200.0

            query = f"""
                WITH target AS (
                    SELECT
                        %(danceability)s AS danceability,
                        %(energy)s AS energy,
                        %(speechiness)s AS speechiness,
                        %(acousticness)s AS acousticness,
                        %(instrumentalness)s AS instrumentalness,
                        %(liveness)s AS liveness,
                        %(valence)s AS valence,
                        %(tempo_norm)s AS tempo_norm
                )
                SELECT
                    t.track_id AS spotify_track_id,
                    t.name AS track_name,
                    STRING_AGG(DISTINCT a.name, ', ') AS artists,
                    alb.name AS album_name,
                    t.track_genre,
                    t.popularity,
                    t.duration_ms,
                    t.explicit,
                    af.danceability,
                    af.energy,
                    af.speechiness,
                    af.acousticness,
                    af.instrumentalness,
                    af.liveness,
                    af.valence,
                    af.tempo,
                    af.loudness,
                    af.key,
                    af.mode,
                    af.time_signature,
                    -- Cosine similarity calculation
                    (
                        (af.danceability * tgt.danceability) +
                        (af.energy * tgt.energy) +
                        (af.speechiness * tgt.speechiness) +
                        (af.acousticness * tgt.acousticness) +
                        (af.instrumentalness * tgt.instrumentalness) +
                        (af.liveness * tgt.liveness) +
                        (af.valence * tgt.valence) +
                        ((af.tempo / 200.0) * tgt.tempo_norm)
                    ) / (
                        SQRT(
                            POW(af.danceability, 2) + POW(af.energy, 2) +
                            POW(af.speechiness, 2) + POW(af.acousticness, 2) +
                            POW(af.instrumentalness, 2) + POW(af.liveness, 2) +
                            POW(af.valence, 2) + POW(af.tempo / 200.0, 2)
                        ) *
                        SQRT(
                            POW(tgt.danceability, 2) + POW(tgt.energy, 2) +
                            POW(tgt.speechiness, 2) + POW(tgt.acousticness, 2) +
                            POW(tgt.instrumentalness, 2) + POW(tgt.liveness, 2) +
                            POW(tgt.valence, 2) + POW(tgt.tempo_norm, 2)
                        )
                    ) AS similarity_score
                FROM tracks t
                JOIN audio_features af ON t.id = af.track_id
                LEFT JOIN albums alb ON t.album_id = alb.id
                LEFT JOIN track_artists ta ON t.id = ta.track_id
                LEFT JOIN artists a ON ta.artist_id = a.id
                CROSS JOIN target tgt
                WHERE
                    af.danceability IS NOT NULL
                    AND af.energy IS NOT NULL
                    AND af.valence IS NOT NULL
                    AND af.tempo IS NOT NULL
                    AND af.time_signature IS NOT NULL
                    AND t.duration_ms IS NOT NULL
                    {exclude_clause}
                GROUP BY t.id, t.track_id, t.name, alb.name, t.track_genre, t.popularity,
                         t.duration_ms, t.explicit,
                         af.danceability, af.energy, af.speechiness, af.acousticness,
                         af.instrumentalness, af.liveness, af.valence, af.tempo, af.loudness,
                         af.key, af.mode, af.time_signature,
                         tgt.danceability, tgt.energy, tgt.speechiness, tgt.acousticness,
                         tgt.instrumentalness, tgt.liveness, tgt.valence, tgt.tempo_norm
                ORDER BY similarity_score DESC
                LIMIT %(limit)s
            """

            query_params = {
                'danceability': seed_features.get('danceability', 0.5),
                'energy': seed_features.get('energy', 0.5),
                'speechiness': seed_features.get('speechiness', 0.1),
                'acousticness': seed_features.get('acousticness', 0.5),
                'instrumentalness': seed_features.get('instrumentalness', 0.0),
                'liveness': seed_features.get('liveness', 0.1),
                'valence': seed_features.get('valence', 0.5),
                'tempo_norm': seed_tempo_norm,
                'limit': limit,
                'exclude_ids': tuple(exclude_ids) if exclude_ids else tuple()
            }

            cursor.execute(query, query_params)
            results = cursor.fetchall()
            cursor.close()

            return [self._row_to_track(dict(row)) for row in results]

    def get_random_tracks(self, limit: int = 10, genre: str = None) -> List[Track]:
        """Get random tracks for exploration"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            genre_clause = "WHERE track_genre = %s" if genre else ""
            params = [genre, limit] if genre else [limit]

            query = f"""
                SELECT
                    spotify_track_id,
                    track_name,
                    artists,
                    album_name,
                    track_genre,
                    popularity,
                    duration_ms,
                    explicit,
                    danceability,
                    energy,
                    speechiness,
                    acousticness,
                    instrumentalness,
                    liveness,
                    valence,
                    tempo,
                    loudness,
                    key,
                    mode,
                    time_signature
                FROM v_tracks_complete
                {genre_clause}
                ORDER BY RANDOM()
                LIMIT %s
            """

            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()

            return [self._row_to_track(dict(row)) for row in results]


    def get_artist_ids_for_tracks(self, spotify_ids: List[str]) -> Dict[str, List[int]]:
        """Map Spotify track IDs to their artist internal IDs. """
        if not spotify_ids:
            return {}

        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT t.track_id AS spotify_track_id, ta.artist_id
                FROM tracks t
                JOIN track_artists ta ON t.id = ta.track_id
                WHERE t.track_id = ANY(%s)
            """, (spotify_ids,))

            results = cursor.fetchall()
            cursor.close()

            mapping: Dict[str, List[int]] = {}
            for row in results:
                sid = row['spotify_track_id']
                if sid not in mapping:
                    mapping[sid] = []
                mapping[sid].append(row['artist_id'])
            return mapping

    def get_artist_relationships_bfs(
        self, artist_ids: List[int], max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """BFS traversal of artist relationships from seed artists.  """
        if not artist_ids:
            return []

        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                WITH RECURSIVE bfs AS (
                    -- Base case: seed artists at depth 0
                    SELECT
                        unnest(%(seeds)s::int[]) AS artist_id,
                        0 AS depth,
                        1.0::float AS weight,
                        'seed'::varchar AS relationship_type

                    UNION

                    -- Recursive step: follow edges
                    SELECT
                        CASE
                            WHEN ar.artist_id_1 = bfs.artist_id THEN ar.artist_id_2
                            ELSE ar.artist_id_1
                        END AS artist_id,
                        bfs.depth + 1 AS depth,
                        ar.weight,
                        ar.relationship_type
                    FROM bfs
                    JOIN artist_relationships ar
                        ON (ar.artist_id_1 = bfs.artist_id OR ar.artist_id_2 = bfs.artist_id)
                    WHERE bfs.depth < %(max_depth)s
                )
                SELECT DISTINCT ON (artist_id)
                    artist_id,
                    depth,
                    weight,
                    relationship_type
                FROM bfs
                WHERE depth > 0
                ORDER BY artist_id, depth ASC, weight DESC
            """, {'seeds': artist_ids, 'max_depth': max_depth})

            results = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            return results

    def get_genre_similarity(self, genre_1: str, genre_2: str) -> float:
        """Look up genre similarity.   """
        if genre_1 == genre_2:
            return 1.0

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT similarity FROM genre_similarity
                WHERE genre_1 = %s AND genre_2 = %s
            """, (genre_1, genre_2))

            result = cursor.fetchone()
            cursor.close()
            return float(result[0]) if result else 0.0

    def get_candidate_artist_ids(self, track_db_ids: List[int]) -> Dict[int, List[int]]:
        """Map internal track IDs to their artist IDs.  """
        if not track_db_ids:
            return {}

        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT track_id, artist_id
                FROM track_artists
                WHERE track_id = ANY(%s)
            """, (track_db_ids,))

            results = cursor.fetchall()
            cursor.close()

            mapping: Dict[int, List[int]] = {}
            for row in results:
                tid = row['track_id']
                if tid not in mapping:
                    mapping[tid] = []
                mapping[tid].append(row['artist_id'])
            return mapping


# Global database instance
db = Database()
