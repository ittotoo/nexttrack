"""NextTrack Database Loader"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import sys
from pathlib import Path

# Database connection parameters
DB_CONFIG = {
    'dbname': 'nexttrack',
    'user': 'postgres',  
    'password': 'postgres',  
    'host': 'localhost',
    'port': 5432
}

# Dataset path
DATASET_PATH = Path(__file__).parent.parent.parent / 'Data' / 'dataset.csv'


def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"Connected to database: {DB_CONFIG['dbname']}")
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)


def load_dataset():
    """Load and clean the Kaggle dataset"""
    print(f"\nLoading dataset from: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)
    print(f"Loaded {len(df):,} rows")

    # Handle duplicates - keep first occurrence
    original_count = len(df)
    df_clean = df.drop_duplicates(subset=['track_id'], keep='first')
    duplicates_removed = original_count - len(df_clean)

    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed:,} duplicate track_ids")

    print(f"Final dataset: {len(df_clean):,} unique tracks")

    return df_clean


def load_artists(conn, df):
    """Load artists table (normalized)"""
    print("\nLoading artists...")

    # Extract all unique artists from the comma-separated field
    all_artists = set()
    for artists_str in df['artists'].dropna():
        # Split by common separators
        artists_list = [a.strip() for a in str(artists_str).replace(';', ',').split(',')]
        all_artists.update(artists_list)

    all_artists = sorted(list(all_artists))
    print(f"   Found {len(all_artists):,} unique artists")

    # Insert artists
    cursor = conn.cursor()
    insert_query = "INSERT INTO artists (name) VALUES %s ON CONFLICT DO NOTHING"
    execute_values(cursor, insert_query, [(name,) for name in all_artists])
    conn.commit()

    print(f"Inserted {len(all_artists):,} artists")

    # Return artist_name -> id mapping
    cursor.execute("SELECT id, name FROM artists")
    artist_map = {name: id for id, name in cursor.fetchall()}
    cursor.close()

    return artist_map


def load_albums(conn, df):
    """Load albums table (normalized)"""
    print("\nLoading albums...")

    unique_albums = df['album_name'].dropna().unique()
    print(f"   Found {len(unique_albums):,} unique albums")

    cursor = conn.cursor()
    insert_query = "INSERT INTO albums (name) VALUES %s ON CONFLICT DO NOTHING"
    execute_values(cursor, insert_query, [(name,) for name in unique_albums])
    conn.commit()

    print(f"Inserted {len(unique_albums):,} albums")

    # Return album_name -> id mapping
    cursor.execute("SELECT id, name FROM albums")
    album_map = {name: id for id, name in cursor.fetchall()}
    cursor.close()

    return album_map


def load_tracks(conn, df, album_map):
    """Load tracks table"""
    print("\nLoading tracks...")

    cursor = conn.cursor()

    tracks_data = []
    skipped = 0

    for _, row in df.iterrows():
        # Validate required fields
        if pd.isna(row['track_id']) or pd.isna(row['track_name']):
            skipped += 1
            continue

        # Validate duration_ms (must be > 0)
        duration_ms = int(row['duration_ms']) if pd.notna(row['duration_ms']) else 0
        if duration_ms <= 0:
            skipped += 1
            continue

        album_id = album_map.get(row['album_name'])

        tracks_data.append((
            row['track_id'],
            str(row['track_name']),  # Ensure it's a string
            album_id,
            int(row['popularity']) if pd.notna(row['popularity']) else 0,
            duration_ms,
            bool(row['explicit']) if pd.notna(row['explicit']) else False,
            row['track_genre'] if pd.notna(row['track_genre']) else None
        ))

    if skipped > 0:
        print(f"   Skipped {skipped:,} tracks with invalid data (NaN names or duration <= 0)")

    insert_query = """
        INSERT INTO tracks (track_id, name, album_id, popularity, duration_ms, explicit, track_genre)
        VALUES %s
        ON CONFLICT (track_id) DO NOTHING
    """
    execute_values(cursor, insert_query, tracks_data)
    conn.commit()

    print(f"Inserted {len(tracks_data):,} tracks")

    # Return track_id -> id mapping
    cursor.execute("SELECT id, track_id FROM tracks")
    track_map = {track_id: id for id, track_id in cursor.fetchall()}
    cursor.close()

    return track_map


def load_track_artists(conn, df, artist_map, track_map):
    """Load track_artists many-to-many relationships"""
    print("\nLoading track-artist relationships...")

    cursor = conn.cursor()
    relationships = []

    for _, row in df.iterrows():
        track_id = track_map.get(row['track_id'])
        if not track_id:
            continue

        # Parse artists
        artists_str = str(row['artists'])
        artists_list = [a.strip() for a in artists_str.replace(';', ',').split(',')]

        for position, artist_name in enumerate(artists_list, start=1):
            artist_id = artist_map.get(artist_name)
            if artist_id:
                relationships.append((track_id, artist_id, position))

    insert_query = """
        INSERT INTO track_artists (track_id, artist_id, artist_position)
        VALUES %s
        ON CONFLICT (track_id, artist_id) DO NOTHING
    """
    execute_values(cursor, insert_query, relationships)
    conn.commit()

    print(f"Inserted {len(relationships):,} track-artist relationships")
    cursor.close()


def load_audio_features(conn, df, track_map):
    """Load audio_features table"""
    print("\nLoading audio features...")

    cursor = conn.cursor()

    features_data = []
    skipped = 0

    for _, row in df.iterrows():
        track_id = track_map.get(row['track_id'])
        if not track_id:
            skipped += 1
            continue

        # Validate tempo (must be > 0 if present)
        tempo = float(row['tempo']) if pd.notna(row['tempo']) else None
        if tempo is not None and tempo <= 0:
            tempo = None  # Set to NULL instead of invalid value

        # Validate key (must be 0-11)
        key = int(row['key']) if pd.notna(row['key']) else None
        if key is not None and (key < 0 or key > 11):
            key = None

        # Validate mode (must be 0 or 1)
        mode = int(row['mode']) if pd.notna(row['mode']) else None
        if mode is not None and mode not in (0, 1):
            mode = None

        # Validate time_signature (must be 1-7)
        time_signature = int(row['time_signature']) if pd.notna(row['time_signature']) else None
        if time_signature is not None and (time_signature < 1 or time_signature > 7):
            time_signature = None

        features_data.append((
            track_id,
            float(row['danceability']) if pd.notna(row['danceability']) else None,
            float(row['energy']) if pd.notna(row['energy']) else None,
            float(row['speechiness']) if pd.notna(row['speechiness']) else None,
            float(row['acousticness']) if pd.notna(row['acousticness']) else None,
            float(row['instrumentalness']) if pd.notna(row['instrumentalness']) else None,
            float(row['liveness']) if pd.notna(row['liveness']) else None,
            float(row['valence']) if pd.notna(row['valence']) else None,
            tempo,
            float(row['loudness']) if pd.notna(row['loudness']) else None,
            key,
            mode,
            time_signature
        ))

    if skipped > 0:
        print(f"   Skipped {skipped:,} tracks not found in track_map")

    insert_query = """
        INSERT INTO audio_features (
            track_id, danceability, energy, speechiness, acousticness,
            instrumentalness, liveness, valence, tempo, loudness,
            key, mode, time_signature
        )
        VALUES %s
        ON CONFLICT (track_id) DO NOTHING
    """
    execute_values(cursor, insert_query, features_data)
    conn.commit()

    print(f"Inserted {len(features_data):,} audio feature records")
    cursor.close()


def verify_data(conn):
    """Verify loaded data"""
    print("\n✓ Verifying data...")

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM artists")
    print(f"   Artists: {cursor.fetchone()[0]:,}")

    cursor.execute("SELECT COUNT(*) FROM albums")
    print(f"   Albums: {cursor.fetchone()[0]:,}")

    cursor.execute("SELECT COUNT(*) FROM tracks")
    print(f"   Tracks: {cursor.fetchone()[0]:,}")

    cursor.execute("SELECT COUNT(*) FROM track_artists")
    print(f"   Track-Artist relationships: {cursor.fetchone()[0]:,}")

    cursor.execute("SELECT COUNT(*) FROM audio_features")
    print(f"   Audio features: {cursor.fetchone()[0]:,}")

    # Test the view
    cursor.execute("SELECT COUNT(*) FROM v_tracks_complete")
    print(f"   Complete track view: {cursor.fetchone()[0]:,} rows")

    cursor.close()


def main():
    """Main execution"""
    print("=" * 60)
    print("NextTrack Database Loader")
    print("=" * 60)

    # Load dataset
    df = load_dataset()

    # Connect to database
    conn = connect_db()

    try:
        # Load data in order (respecting foreign keys)
        artist_map = load_artists(conn, df)
        album_map = load_albums(conn, df)
        track_map = load_tracks(conn, df, album_map)
        load_track_artists(conn, df, artist_map, track_map)
        load_audio_features(conn, df, track_map)

        # Verify
        verify_data(conn)

        print("\n" + "=" * 60)
        print("DATABASE LOADING COMPLETE!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during loading: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
