"""Populate knowledge graph tables from existing database data."""

import sys
import os
import logging
import time

import psycopg2
from psycopg2.extras import execute_values

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.recommender.genre_taxonomy import (
    GENRE_TO_SUPERGENRE,
    get_genre_similarity,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_connection():
    return psycopg2.connect(
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
    )


def populate_artist_collaborations(conn):
    """Find artist pairs who share tracks """
    logger.info("Finding artist collaborations from shared tracks...")
    cursor = conn.cursor()

    # Find all artist pairs that appear on the same track
    cursor.execute("""
        INSERT INTO artist_relationships (artist_id_1, artist_id_2, relationship_type, weight, evidence_count)
        SELECT
            ta1.artist_id AS artist_id_1,
            ta2.artist_id AS artist_id_2,
            'collaboration' AS relationship_type,
            1.0 AS weight,
            COUNT(*) AS evidence_count
        FROM track_artists ta1
        JOIN track_artists ta2
            ON ta1.track_id = ta2.track_id
            AND ta1.artist_id < ta2.artist_id
        GROUP BY ta1.artist_id, ta2.artist_id
        ON CONFLICT (artist_id_1, artist_id_2, relationship_type) DO UPDATE
            SET evidence_count = EXCLUDED.evidence_count
    """)

    count = cursor.rowcount
    conn.commit()
    cursor.close()
    logger.info(f"Inserted {count} collaboration relationships")
    return count


def populate_shared_album_relationships(conn):
    """Find artist pairs who have different tracks on the same album. """
    logger.info("Finding shared album relationships...")
    cursor = conn.cursor()

    # Artists with different tracks on the same album (excludes collaborations
    # already found — only counts cases where artists have SEPARATE tracks on same album)
    cursor.execute("""
        INSERT INTO artist_relationships (artist_id_1, artist_id_2, relationship_type, weight, evidence_count)
        SELECT
            a1.artist_id AS artist_id_1,
            a2.artist_id AS artist_id_2,
            'shared_album' AS relationship_type,
            0.7 AS weight,
            COUNT(DISTINCT t1.album_id) AS evidence_count
        FROM track_artists a1
        JOIN tracks t1 ON a1.track_id = t1.id
        JOIN tracks t2 ON t1.album_id = t2.album_id AND t1.id != t2.id
        JOIN track_artists a2 ON t2.id = a2.track_id
        WHERE a1.artist_id < a2.artist_id
            AND t1.album_id IS NOT NULL
        GROUP BY a1.artist_id, a2.artist_id
        ON CONFLICT (artist_id_1, artist_id_2, relationship_type) DO UPDATE
            SET evidence_count = EXCLUDED.evidence_count
    """)

    count = cursor.rowcount
    conn.commit()
    cursor.close()
    logger.info(f"Inserted {count} shared album relationships")
    return count


def populate_genre_similarity(conn):
    """Populate genre similarity matrix from taxonomy hierarchy."""
    logger.info("Populating genre similarity matrix...")
    cursor = conn.cursor()

    # Get all unique genres from the database
    cursor.execute("SELECT DISTINCT track_genre FROM tracks WHERE track_genre IS NOT NULL")
    db_genres = [row[0] for row in cursor.fetchall()]
    logger.info(f"Found {len(db_genres)} genres in database")

    # Build all genre pairs with similarity scores
    rows = []
    for g1 in db_genres:
        for g2 in db_genres:
            sim = get_genre_similarity(g1, g2)
            rows.append((g1, g2, sim))

    # Bulk insert
    execute_values(
        cursor,
        """
        INSERT INTO genre_similarity (genre_1, genre_2, similarity)
        VALUES %s
        ON CONFLICT (genre_1, genre_2) DO UPDATE SET similarity = EXCLUDED.similarity
        """,
        rows,
    )

    conn.commit()
    cursor.close()
    logger.info(f"Inserted {len(rows)} genre similarity pairs")
    return len(rows)


def print_statistics(conn):
    """Print summary statistics of the knowledge graph."""
    cursor = conn.cursor()

    cursor.execute("SELECT relationship_type, COUNT(*), AVG(evidence_count) FROM artist_relationships GROUP BY relationship_type")
    print("\n=== Artist Relationships ===")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} edges (avg {row[2]:.1f} evidence)")

    cursor.execute("SELECT COUNT(*) FROM genre_similarity WHERE similarity > 0")
    nonzero = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM genre_similarity")
    total = cursor.fetchone()[0]
    print(f"\n=== Genre Similarity ===")
    print(f"  Total pairs: {total}")
    print(f"  Non-zero similarity: {nonzero}")

    cursor.close()


if __name__ == "__main__":
    start = time.time()
    logger.info("Starting knowledge graph population...")

    conn = get_connection()

    # Clear existing data for clean repopulation
    cursor = conn.cursor()
    cursor.execute("DELETE FROM artist_relationships")
    cursor.execute("DELETE FROM genre_similarity")
    conn.commit()
    cursor.close()

    collab_count = populate_artist_collaborations(conn)
    album_count = populate_shared_album_relationships(conn)
    genre_count = populate_genre_similarity(conn)

    print_statistics(conn)

    conn.close()

    elapsed = time.time() - start
    logger.info(f"Knowledge graph population complete in {elapsed:.1f}s")
    logger.info(f"Total: {collab_count} collaborations, {album_count} shared albums, {genre_count} genre pairs")
