-- NextTrack Database Schema (Normalized - Option B)

DROP TABLE IF EXISTS track_artists CASCADE;
DROP TABLE IF EXISTS audio_features CASCADE;
DROP TABLE IF EXISTS tracks CASCADE;
DROP TABLE IF EXISTS albums CASCADE;
DROP TABLE IF EXISTS artists CASCADE;

CREATE TABLE artists (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    spotify_id VARCHAR(50),  -- For future Spotify API integration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Unique constraint on name to avoid duplicates
CREATE UNIQUE INDEX idx_artist_name ON artists(name);


CREATE TABLE albums (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    spotify_id VARCHAR(50),  -- For future Spotify API integration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster lookups
CREATE INDEX idx_album_name ON albums(name);


CREATE TABLE tracks (
    id SERIAL PRIMARY KEY,
    track_id VARCHAR(50) UNIQUE NOT NULL,  -- Spotify track ID (unique!)
    name TEXT NOT NULL,
    album_id INTEGER REFERENCES albums(id) ON DELETE SET NULL,

    -- Track attributes
    popularity INTEGER CHECK (popularity >= 0 AND popularity <= 100),
    duration_ms INTEGER CHECK (duration_ms > 0),
    explicit BOOLEAN DEFAULT FALSE,
    track_genre VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast queries
CREATE UNIQUE INDEX idx_track_spotify_id ON tracks(track_id);
CREATE INDEX idx_track_genre ON tracks(track_genre);
CREATE INDEX idx_track_popularity ON tracks(popularity);
CREATE INDEX idx_track_album ON tracks(album_id);


CREATE TABLE track_artists (
    track_id INTEGER REFERENCES tracks(id) ON DELETE CASCADE,
    artist_id INTEGER REFERENCES artists(id) ON DELETE CASCADE,
    artist_position INTEGER DEFAULT 1,  -- Order for featured artists
    PRIMARY KEY (track_id, artist_id)
);

-- Indexes for fast lookups
CREATE INDEX idx_track_artists_track ON track_artists(track_id);
CREATE INDEX idx_track_artists_artist ON track_artists(artist_id);


CREATE TABLE audio_features (
    track_id INTEGER PRIMARY KEY REFERENCES tracks(id) ON DELETE CASCADE,

    -- Normalized features (0-1 range) - from Spotify API
    danceability FLOAT CHECK (danceability >= 0 AND danceability <= 1),
    energy FLOAT CHECK (energy >= 0 AND energy <= 1),
    speechiness FLOAT CHECK (speechiness >= 0 AND speechiness <= 1),
    acousticness FLOAT CHECK (acousticness >= 0 AND acousticness <= 1),
    instrumentalness FLOAT CHECK (instrumentalness >= 0 AND instrumentalness <= 1),
    liveness FLOAT CHECK (liveness >= 0 AND liveness <= 1),
    valence FLOAT CHECK (valence >= 0 AND valence <= 1),

    -- Other audio attributes (not normalized)
    tempo FLOAT CHECK (tempo > 0),
    loudness FLOAT,
    key INTEGER CHECK (key >= 0 AND key <= 11),  -- 0-11 for C, C#, D, ..., B
    mode INTEGER CHECK (mode IN (0, 1)),  -- 0 = minor, 1 = major
    time_signature INTEGER CHECK (time_signature >= 1 AND time_signature <= 7),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast feature-based queries
CREATE INDEX idx_audio_features_energy ON audio_features(energy);
CREATE INDEX idx_audio_features_valence ON audio_features(valence);
CREATE INDEX idx_audio_features_danceability ON audio_features(danceability);



-- Complete track information with artists and features
CREATE OR REPLACE VIEW v_tracks_complete AS
SELECT
    t.id,
    t.track_id AS spotify_track_id,
    t.name AS track_name,
    t.popularity,
    t.duration_ms,
    t.explicit,
    t.track_genre,

    -- Album info
    alb.name AS album_name,

    -- Artists (comma-separated for simplicity in queries)
    STRING_AGG(art.name, ', ' ORDER BY ta.artist_position) AS artists,

    -- Audio features
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
    af.time_signature

FROM tracks t
LEFT JOIN albums alb ON t.album_id = alb.id
LEFT JOIN track_artists ta ON t.id = ta.track_id
LEFT JOIN artists art ON ta.artist_id = art.id
LEFT JOIN audio_features af ON t.id = af.track_id
GROUP BY t.id, alb.name, af.danceability, af.energy, af.speechiness,
         af.acousticness, af.instrumentalness, af.liveness, af.valence,
         af.tempo, af.loudness, af.key, af.mode, af.time_signature;



-- Function to get tracks similar by audio features (cosine similarity)
CREATE OR REPLACE FUNCTION get_similar_tracks(
    target_track_id INTEGER,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    track_id INTEGER,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH target AS (
        SELECT
            danceability, energy, speechiness, acousticness,
            instrumentalness, liveness, valence, tempo / 200.0 AS tempo_norm
        FROM audio_features
        WHERE audio_features.track_id = target_track_id
    )
    SELECT
        af.track_id,
        -- Cosine similarity calculation
        (
            (af.danceability * t.danceability) +
            (af.energy * t.energy) +
            (af.speechiness * t.speechiness) +
            (af.acousticness * t.acousticness) +
            (af.instrumentalness * t.instrumentalness) +
            (af.liveness * t.liveness) +
            (af.valence * t.valence) +
            (af.tempo / 200.0 * t.tempo_norm)
        ) / (
            SQRT(
                POW(af.danceability, 2) + POW(af.energy, 2) +
                POW(af.speechiness, 2) + POW(af.acousticness, 2) +
                POW(af.instrumentalness, 2) + POW(af.liveness, 2) +
                POW(af.valence, 2) + POW(af.tempo / 200.0, 2)
            ) *
            SQRT(
                POW(t.danceability, 2) + POW(t.energy, 2) +
                POW(t.speechiness, 2) + POW(t.acousticness, 2) +
                POW(t.instrumentalness, 2) + POW(t.liveness, 2) +
                POW(t.valence, 2) + POW(t.tempo_norm, 2)
            )
        ) AS similarity_score
    FROM audio_features af
    CROSS JOIN target t
    WHERE af.track_id != target_track_id
    ORDER BY similarity_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;


COMMENT ON TABLE artists IS 'Artist master table - normalized to avoid duplication';
COMMENT ON TABLE albums IS 'Album master table';
COMMENT ON TABLE tracks IS 'Core track metadata without audio features';
COMMENT ON TABLE track_artists IS 'Many-to-many relationship for track collaborations';
COMMENT ON TABLE audio_features IS 'Normalized audio feature data from Spotify API';

COMMENT ON COLUMN tracks.track_id IS 'Spotify track ID (unique identifier)';
COMMENT ON COLUMN tracks.popularity IS 'Spotify popularity score (0-100)';
COMMENT ON COLUMN audio_features.danceability IS 'How suitable for dancing (0-1)';
COMMENT ON COLUMN audio_features.energy IS 'Intensity and activity (0-1)';
COMMENT ON COLUMN audio_features.valence IS 'Musical positiveness (0-1)';
COMMENT ON COLUMN audio_features.tempo IS 'Overall tempo in BPM';


